#!/usr/bin/env python3
"""Reproduce one fixture evaluation from a frozen lock in a fresh environment.

This harness is deliberately offline and no-clobber.  It copies a small,
hash-backed project snapshot into a new evidence root, installs that snapshot
from an unchanged ``uv.lock`` into a new Python 3.11 virtual environment, and
runs the existing fixture reproducibility command from the non-editable install.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import tomllib
import urllib.parse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence


EXPECTED_PROJECT_NAME = "evidence-inspector"
EXPECTED_PROJECT_PYTHON = ">=3.11,<3.12"
EXPECTED_LOCK_PYTHON = "==3.11.*"
EXPECTED_BUILD_BACKEND = "hatchling.build"
EXPECTED_BUILD_REQUIREMENT = "hatchling==1.31.0"
EXPECTED_BUILD_PACKAGE = "hatchling"
EXPECTED_BUILD_VERSION = "1.31.0"
OFFICIAL_REGISTRY = "https://pypi.org/simple"
OFFICIAL_ARTIFACT_HOST = "files.pythonhosted.org"
FIXED_SNAPSHOT_FILES = (
    Path("pyproject.toml"),
    Path("uv.lock"),
    Path("README.md"),
    Path("examples/sample_bundle.json"),
    Path("scripts/check_fixture_reproducibility.py"),
)
SAFE_ENVIRONMENT_KEYS = (
    "HOME",
    "LANG",
    "LC_ALL",
    "PATH",
    "SYSTEMROOT",
    "TMPDIR",
    "USERPROFILE",
)


class HarnessError(RuntimeError):
    """A fail-closed precondition or reproduction failure."""


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: list[str]
    exit_code: int | None
    timed_out: bool
    duration_seconds: float
    stdout_path: str
    stderr_path: str
    stdout_sha256: str
    stderr_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "command": self.command,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "duration_seconds": self.duration_seconds,
            "stdout_path": self.stdout_path,
            "stderr_path": self.stderr_path,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
        }


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_bytes_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)


def _write_json_exclusive(path: Path, value: object) -> None:
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    _write_bytes_exclusive(path, (payload + "\n").encode("utf-8"))


def validate_locked_metadata(project_root: Path) -> dict[str, Any]:
    """Fail unless both project metadata and the lock require Python 3.11."""

    try:
        pyproject = tomllib.loads(
            (project_root / "pyproject.toml").read_text(encoding="utf-8")
        )
        project = pyproject["project"]
        build_system = pyproject["build-system"]
        lock = tomllib.loads((project_root / "uv.lock").read_text(encoding="utf-8"))
    except (KeyError, OSError, tomllib.TOMLDecodeError) as exc:
        raise HarnessError(f"cannot read locked project metadata: {exc}") from exc

    if project.get("name") != EXPECTED_PROJECT_NAME:
        raise HarnessError(
            f"expected project name {EXPECTED_PROJECT_NAME!r}; "
            f"received {project.get('name')!r}"
        )
    if project.get("requires-python") != EXPECTED_PROJECT_PYTHON:
        raise HarnessError(
            "pyproject.toml must retain the audited Python requirement "
            f"{EXPECTED_PROJECT_PYTHON!r}"
        )
    if lock.get("requires-python") != EXPECTED_LOCK_PYTHON:
        raise HarnessError(
            f"uv.lock must retain requires-python = {EXPECTED_LOCK_PYTHON!r}"
        )
    if build_system.get("build-backend") != EXPECTED_BUILD_BACKEND:
        raise HarnessError(
            f"pyproject.toml must retain build-backend = {EXPECTED_BUILD_BACKEND!r}"
        )
    if build_system.get("requires") != [EXPECTED_BUILD_REQUIREMENT]:
        raise HarnessError(
            "pyproject.toml must retain the audited exact build requirement "
            f"{EXPECTED_BUILD_REQUIREMENT!r}"
        )
    if EXPECTED_BUILD_REQUIREMENT not in project.get("optional-dependencies", {}).get(
        "dev", []
    ):
        raise HarnessError(
            f"the dev extra must lock the build requirement {EXPECTED_BUILD_REQUIREMENT!r}"
        )
    locked_project = [
        package
        for package in lock.get("package", [])
        if package.get("name") == EXPECTED_PROJECT_NAME
    ]
    if len(locked_project) != 1 or locked_project[0].get("version") != project.get(
        "version"
    ):
        raise HarnessError("uv.lock does not contain exactly one matching project version")
    locked_build_packages = [
        package
        for package in lock.get("package", [])
        if package.get("name") == EXPECTED_BUILD_PACKAGE
    ]
    if (
        len(locked_build_packages) != 1
        or locked_build_packages[0].get("version") != EXPECTED_BUILD_VERSION
        or locked_build_packages[0].get("source", {}).get("registry")
        != OFFICIAL_REGISTRY
    ):
        raise HarnessError(
            "uv.lock must contain exactly one official-registry build backend "
            f"{EXPECTED_BUILD_PACKAGE}=={EXPECTED_BUILD_VERSION}"
        )
    artifact_count = 0
    for package in lock.get("package", []):
        source = package.get("source", {})
        registry = source.get("registry")
        if registry is None:
            if package.get("name") != EXPECTED_PROJECT_NAME or source.get("editable") != ".":
                raise HarnessError(
                    f"unsupported non-registry lock source for {package.get('name')!r}"
                )
            continue
        if registry != OFFICIAL_REGISTRY:
            raise HarnessError(
                f"non-official registry in uv.lock for {package.get('name')!r}: {registry!r}"
            )
        artifacts = list(package.get("wheels", []))
        if package.get("sdist"):
            artifacts.append(package["sdist"])
        if not artifacts:
            raise HarnessError(f"locked registry package has no artifacts: {package.get('name')}")
        for artifact in artifacts:
            parsed = urllib.parse.urlsplit(str(artifact.get("url", "")))
            digest = str(artifact.get("hash", ""))
            size = artifact.get("size")
            if (
                parsed.scheme != "https"
                or parsed.hostname != OFFICIAL_ARTIFACT_HOST
                or parsed.username is not None
                or parsed.password is not None
                or parsed.query
                or parsed.fragment
            ):
                raise HarnessError(
                    f"non-official artifact URL in uv.lock for {package.get('name')!r}"
                )
            if re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
                raise HarnessError(
                    f"missing SHA-256 artifact lock for {package.get('name')!r}"
                )
            if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
                raise HarnessError(f"invalid locked artifact size for {package.get('name')!r}")
            artifact_count += 1
    return {
        "project_name": EXPECTED_PROJECT_NAME,
        "project_version": str(project["version"]),
        "project_requires_python": str(project["requires-python"]),
        "lock_requires_python": str(lock["requires-python"]),
        "build_backend": EXPECTED_BUILD_BACKEND,
        "build_requirement": EXPECTED_BUILD_REQUIREMENT,
        "locked_build_backend_version": EXPECTED_BUILD_VERSION,
        "pyproject_sha256": _sha256_file(project_root / "pyproject.toml"),
        "uv_lock_sha256": _sha256_file(project_root / "uv.lock"),
        "locked_artifact_count": artifact_count,
        "locked_artifact_host": OFFICIAL_ARTIFACT_HOST,
        "locked_registry": OFFICIAL_REGISTRY,
    }


def build_sanitized_environment(
    source: Mapping[str, str] | None = None,
    *,
    allow_dependency_downloads: bool = False,
) -> dict[str, str]:
    """Return a minimal environment with fixture mode and no credentials."""

    values = os.environ if source is None else source
    clean = {key: values[key] for key in SAFE_ENVIRONMENT_KEYS if values.get(key)}
    clean.update(
        {
            "EVIDENCE_INSPECTOR_GATEWAY": "fixture",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "UV_KEYRING_PROVIDER": "disabled",
            "UV_NO_PROGRESS": "1",
            "UV_PYTHON_DOWNLOADS": "never",
        }
    )
    if not allow_dependency_downloads:
        clean["UV_OFFLINE"] = "1"
    return clean


def discover_snapshot_files(project_root: Path) -> tuple[Path, ...]:
    files = list(FIXED_SNAPSHOT_FILES)
    source_root = project_root / "src" / "evidence_inspector"
    files.extend(path.relative_to(project_root) for path in source_root.rglob("*.py"))
    unique = tuple(sorted(set(files), key=lambda item: item.as_posix()))
    for relative in unique:
        source = project_root / relative
        if source.is_symlink() or not source.is_file():
            raise HarnessError(f"required snapshot input is missing or a symlink: {relative}")
    return unique


def copy_snapshot(project_root: Path, checkout: Path) -> list[dict[str, Any]]:
    """Copy the explicit input set without overwriting any destination path."""

    checkout.mkdir(parents=False, exist_ok=False)
    manifest: list[dict[str, Any]] = []
    for relative in discover_snapshot_files(project_root):
        source = project_root / relative
        destination = checkout / relative
        payload = source.read_bytes()
        _write_bytes_exclusive(destination, payload)
        source_hash = _sha256_bytes(payload)
        copied_hash = _sha256_file(destination)
        if copied_hash != source_hash:
            raise HarnessError(f"snapshot hash mismatch after copying {relative}")
        manifest.append(
            {
                "path": relative.as_posix(),
                "bytes": len(payload),
                "sha256": source_hash,
            }
        )
    return manifest


def prepare_new_run_root(path: Path) -> Path:
    """Atomically claim a new root; an existing path is never reused."""

    candidate = path.expanduser().absolute()
    if os.path.lexists(candidate):
        raise HarnessError(f"refusing to reuse clean-environment root: {candidate}")
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.mkdir(exist_ok=False)
    return candidate


def _relative_log_path(path: Path, run_root: Path) -> str:
    return path.relative_to(run_root).as_posix()


def run_command(
    *,
    name: str,
    command: Sequence[str],
    cwd: Path,
    environment: Mapping[str, str],
    logs_dir: Path,
    run_root: Path,
    timeout_seconds: float,
) -> CommandResult:
    """Run one bounded step, retain logs, and raise on every non-zero result."""

    started = time.perf_counter()
    stdout = ""
    stderr = ""
    exit_code: int | None = None
    timed_out = False
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env=dict(environment),
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        exit_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")

    duration = time.perf_counter() - started
    stdout_path = logs_dir / f"{name}.stdout.log"
    stderr_path = logs_dir / f"{name}.stderr.log"
    stdout_payload = stdout.encode("utf-8")
    stderr_payload = stderr.encode("utf-8")
    _write_bytes_exclusive(stdout_path, stdout_payload)
    _write_bytes_exclusive(stderr_path, stderr_payload)
    result = CommandResult(
        name=name,
        command=list(command),
        exit_code=exit_code,
        timed_out=timed_out,
        duration_seconds=duration,
        stdout_path=_relative_log_path(stdout_path, run_root),
        stderr_path=_relative_log_path(stderr_path, run_root),
        stdout_sha256=_sha256_bytes(stdout_payload),
        stderr_sha256=_sha256_bytes(stderr_payload),
    )
    if timed_out:
        raise HarnessError(f"{name} exceeded {timeout_seconds:g} seconds")
    if exit_code != 0:
        raise HarnessError(f"{name} failed with exit code {exit_code}")
    return result


def validate_runtime_probe(probe: Mapping[str, Any], checkout: Path) -> None:
    version = probe.get("version_info")
    if version != [3, 11]:
        raise HarnessError(f"clean runtime must be Python 3.11; received {version!r}")
    raw_origin = probe.get("package_origin")
    if not isinstance(raw_origin, str):
        raise HarnessError("runtime probe did not report the installed package origin")
    package_origin = Path(raw_origin).resolve()
    environment_root = (checkout / ".venv").resolve()
    if not package_origin.is_relative_to(environment_root):
        raise HarnessError(
            "evidence_inspector was not imported from the clean virtual environment"
        )
    packages = probe.get("packages")
    if not isinstance(packages, list) or not packages:
        raise HarnessError("runtime probe did not retain a package inventory")
    if any(
        not isinstance(item, dict)
        or not isinstance(item.get("name"), str)
        or not isinstance(item.get("version"), str)
        for item in packages
    ):
        raise HarnessError("runtime probe package inventory is malformed")
    installed_versions = {
        item["name"].lower(): item["version"] for item in packages
    }
    if installed_versions.get(EXPECTED_BUILD_PACKAGE) != EXPECTED_BUILD_VERSION:
        raise HarnessError(
            "clean runtime did not install the locked build backend "
            f"{EXPECTED_BUILD_PACKAGE}=={EXPECTED_BUILD_VERSION}"
        )


def validate_fixture_evidence(evidence: Mapping[str, Any]) -> None:
    required = {
        "status": "PASS",
        "fixture_only": True,
        "external_api_used": False,
        "input_artifacts_match": True,
        "input_sha256_match": True,
        "match": True,
        "persisted_artifacts_verified": True,
        "process_isolated": True,
    }
    mismatches = {
        key: {"expected": expected, "actual": evidence.get(key)}
        for key, expected in required.items()
        if evidence.get(key) != expected
    }
    if mismatches:
        raise HarnessError(f"fixture evidence failed closed: {mismatches}")
    first_hash = evidence.get("first_normalized_sha256")
    second_hash = evidence.get("second_normalized_sha256")
    if (
        not isinstance(evidence.get("bundle_id"), str)
        or not evidence["bundle_id"]
        or not isinstance(first_hash, str)
        or re.fullmatch(r"[0-9a-f]{64}", first_hash) is None
        or second_hash != first_hash
    ):
        raise HarnessError("fixture evidence is missing a matching normalized SHA-256")


def _runtime_probe_source() -> str:
    return """
import importlib.metadata
import json
import platform
from pathlib import Path
import evidence_inspector

packages = sorted(
    {
        (distribution.metadata.get("Name") or "UNKNOWN", distribution.version)
        for distribution in importlib.metadata.distributions()
    }
)
print(json.dumps({
    "implementation": platform.python_implementation(),
    "package_origin": str(Path(evidence_inspector.__file__).resolve()),
    "packages": [{"name": name, "version": version} for name, version in packages],
    "python": platform.python_version(),
    "version_info": [__import__("sys").version_info.major, __import__("sys").version_info.minor],
}, sort_keys=True))
""".strip()


def execute_reproduction(
    project_root: Path,
    run_root: Path,
    uv_path: str,
    uv_version: str,
    locked_metadata: Mapping[str, Any],
    *,
    allow_dependency_downloads: bool,
) -> dict[str, Any]:
    checkout = run_root / "checkout"
    logs_dir = run_root / "logs"
    evidence_dir = run_root / "evidence"
    logs_dir.mkdir()
    evidence_dir.mkdir()
    snapshot = copy_snapshot(project_root, checkout)
    snapshot_hashes = {item["path"]: item["sha256"] for item in snapshot}
    if snapshot_hashes.get("pyproject.toml") != locked_metadata["pyproject_sha256"]:
        raise HarnessError("pyproject.toml changed between preflight and snapshot")
    if snapshot_hashes.get("uv.lock") != locked_metadata["uv_lock_sha256"]:
        raise HarnessError("uv.lock changed between preflight and snapshot")
    snapshot_payload = json.dumps(snapshot, separators=(",", ":"), sort_keys=True).encode()
    offline_environment = build_sanitized_environment()
    commands: list[dict[str, Any]] = []

    sync_base = [
        uv_path,
        "sync",
        "--directory",
        str(checkout),
        "--locked",
        "--extra",
        "dev",
        "--no-editable",
        "--python",
        "3.11",
        "--no-python-downloads",
        "--link-mode",
        "copy",
        "--keyring-provider",
        "disabled",
        "--no-progress",
        "--no-config",
    ]
    if allow_dependency_downloads:
        dependency_environment = build_sanitized_environment(
            allow_dependency_downloads=True
        )
        dependency_command = sync_base + [
            "--no-install-project",
            "--default-index",
            OFFICIAL_REGISTRY,
        ]
        commands.append(
            run_command(
                name="01_uv_sync_locked_dependencies_public_pypi",
                command=dependency_command,
                cwd=checkout,
                environment=dependency_environment,
                logs_dir=logs_dir,
                run_root=run_root,
                timeout_seconds=600,
            ).as_dict()
        )
        if _sha256_file(checkout / "uv.lock") != locked_metadata["uv_lock_sha256"]:
            raise HarnessError("uv.lock changed during the locked dependency installation")
        commands.append(
            run_command(
                name="02_uv_sync_project_offline",
                command=sync_base + ["--offline"],
                cwd=checkout,
                environment=offline_environment,
                logs_dir=logs_dir,
                run_root=run_root,
                timeout_seconds=600,
            ).as_dict()
        )
        runtime_step_number = 3
    else:
        commands.append(
            run_command(
                name="01_uv_sync_locked_offline",
                command=sync_base + ["--offline"],
                cwd=checkout,
                environment=offline_environment,
                logs_dir=logs_dir,
                run_root=run_root,
                timeout_seconds=600,
            ).as_dict()
        )
        runtime_step_number = 2
    copied_lock_hash = _sha256_file(checkout / "uv.lock")
    if copied_lock_hash != locked_metadata["uv_lock_sha256"]:
        raise HarnessError("uv.lock changed during the locked project installation")

    venv_python = checkout / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not venv_python.is_file():
        raise HarnessError(f"uv did not create the expected interpreter: {venv_python}")

    runtime_result = run_command(
        name=f"{runtime_step_number:02d}_runtime_probe",
        command=[str(venv_python), "-I", "-c", _runtime_probe_source()],
        cwd=checkout,
        environment=offline_environment,
        logs_dir=logs_dir,
        run_root=run_root,
        timeout_seconds=60,
    )
    commands.append(runtime_result.as_dict())
    try:
        runtime_probe = json.loads(
            (run_root / runtime_result.stdout_path).read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError) as exc:
        raise HarnessError(f"runtime probe did not produce valid JSON: {exc}") from exc
    validate_runtime_probe(runtime_probe, checkout)
    inventory_path = evidence_dir / "installed-packages.json"
    _write_json_exclusive(inventory_path, runtime_probe["packages"])

    sample_bundle = checkout / "examples" / "sample_bundle.json"
    validate_result = run_command(
        name=f"{runtime_step_number + 1:02d}_cli_validate",
        command=[
            str(venv_python),
            "-I",
            "-m",
            "evidence_inspector.cli",
            "validate",
            str(sample_bundle),
        ],
        cwd=checkout,
        environment=offline_environment,
        logs_dir=logs_dir,
        run_root=run_root,
        timeout_seconds=60,
    )
    commands.append(validate_result.as_dict())
    try:
        validation = json.loads(
            (run_root / validate_result.stdout_path).read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError) as exc:
        raise HarnessError(f"CLI validation did not produce valid JSON: {exc}") from exc
    if validation.get("valid") is not True:
        raise HarnessError(f"CLI validation failed closed: {validation!r}")

    fixture_report = evidence_dir / "fixture-reproducibility.json"
    fixture_runs = evidence_dir / "fixture-runs"
    fixture_result = run_command(
        name=f"{runtime_step_number + 2:02d}_fixture_reproducibility",
        command=[
            str(venv_python),
            "-I",
            str(checkout / "scripts" / "check_fixture_reproducibility.py"),
            str(sample_bundle),
            "--runs-root",
            str(fixture_runs),
            "--out",
            str(fixture_report),
        ],
        cwd=checkout,
        environment=offline_environment,
        logs_dir=logs_dir,
        run_root=run_root,
        timeout_seconds=120,
    )
    commands.append(fixture_result.as_dict())
    try:
        fixture_evidence = json.loads(fixture_report.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise HarnessError(f"fixture check did not retain valid JSON: {exc}") from exc
    validate_fixture_evidence(fixture_evidence)

    return {
        "schema_version": "1.0",
        "status": "PASS",
        "scope": (
            "LOCKED_PUBLIC_PYPI_INSTALL_FIXTURE_SINGLE_BUNDLE"
            if allow_dependency_downloads
            else "LOCKED_OFFLINE_FIXTURE_SINGLE_BUNDLE"
        ),
        "generated_at": datetime.now(UTC).isoformat(),
        "project": dict(locked_metadata),
        "snapshot": {
            "file_count": len(snapshot),
            "manifest_sha256": _sha256_bytes(snapshot_payload),
            "files": snapshot,
        },
        "installer": {
            "tool": "uv",
            "version": uv_version,
            "locked": True,
            "lock_unchanged": True,
            "dependency_network_allowed": allow_dependency_downloads,
            "index": OFFICIAL_REGISTRY if allow_dependency_downloads else None,
            "offline": not allow_dependency_downloads,
            "project_install_offline": True,
            "network_step_excluded_project": allow_dependency_downloads,
            "python_downloads_allowed": False,
            "editable_install": False,
            "keyring_allowed": False,
        },
        "runtime": {
            key: runtime_probe[key]
            for key in ("implementation", "package_origin", "python", "version_info")
        },
        "installed_packages": {
            "count": len(runtime_probe["packages"]),
            "path": inventory_path.relative_to(run_root).as_posix(),
            "sha256": _sha256_file(inventory_path),
        },
        "fixture": {
            "bundle_id": fixture_evidence["bundle_id"],
            "external_api_used": False,
            "fixture_only": True,
            "normalized_sha256": fixture_evidence["first_normalized_sha256"],
            "report_path": fixture_report.relative_to(run_root).as_posix(),
            "report_sha256": _sha256_file(fixture_report),
        },
        "commands": commands,
        "environment_policy": {
            "copied_environment_keys": sorted(
                key for key in SAFE_ENVIRONMENT_KEYS if os.environ.get(key)
            ),
            "gateway_forced": "fixture",
            "provider_credentials_copied": False,
            "provider_network_path_selected": False,
            "runtime_uv_offline_forced": True,
        },
        "limitations": [
            (
                "Dependency installation was allowed to contact public PyPI; fixture execution remained local."
                if allow_dependency_downloads
                else "A populated local uv cache is required; this evidence is not a vendored wheelhouse."
            ),
            (
                "The project build and fixture execution were offline, but OS-level network isolation was not measured."
                if allow_dependency_downloads
                else "Offline flags and fixture-only code paths are enforced, but OS-level network isolation is not measured."
            ),
            "This single synthetic bundle does not establish frozen-corpus metrics or live-provider behavior.",
            "The exact build backend is declared in pyproject.toml, resolved in uv.lock through the dev extra, and present in the retained installed-package inventory; an offline-cache replay is still not a clean-machine bootstrap.",
        ],
    }


def _detect_uv(environment: Mapping[str, str]) -> tuple[str, str]:
    uv_path = shutil.which("uv", path=environment.get("PATH"))
    if uv_path is None:
        raise HarnessError("uv is required and was not found on PATH")
    try:
        result = subprocess.run(
            [uv_path, "--version"],
            env=dict(environment),
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HarnessError(f"cannot execute uv: {exc}") from exc
    version = result.stdout.strip()
    if result.returncode != 0 or not version.startswith("uv "):
        raise HarnessError("uv --version did not complete successfully")
    return uv_path, version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--work-root",
        type=Path,
        required=True,
        help="new retained evidence directory; existing paths are refused",
    )
    parser.add_argument(
        "--allow-dependency-downloads",
        action="store_true",
        help=(
            "explicitly allow the locked install to use public PyPI; model-provider "
            "network paths and credentials remain disabled"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(__file__).resolve().parents[1]
    if os.path.lexists(args.work_root.expanduser().absolute()):
        print(
            f"error: refusing to reuse clean-environment root: "
            f"{args.work_root.expanduser().absolute()}",
            file=sys.stderr,
        )
        return 2

    try:
        locked_metadata = validate_locked_metadata(project_root)
        environment = build_sanitized_environment()
        uv_path, uv_version = _detect_uv(environment)
        run_root = prepare_new_run_root(args.work_root)
    except HarnessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    manifest_path = run_root / "manifest.json"
    try:
        manifest = execute_reproduction(
            project_root,
            run_root,
            uv_path,
            uv_version,
            locked_metadata,
            allow_dependency_downloads=args.allow_dependency_downloads,
        )
    except (HarnessError, KeyError, OSError, TypeError, ValueError) as exc:
        manifest = {
            "schema_version": "1.0",
            "status": "FAIL",
            "scope": (
                "LOCKED_PUBLIC_PYPI_INSTALL_FIXTURE_SINGLE_BUNDLE"
                if args.allow_dependency_downloads
                else "LOCKED_OFFLINE_FIXTURE_SINGLE_BUNDLE"
            ),
            "generated_at": datetime.now(UTC).isoformat(),
            "error": str(exc),
            "project": dict(locked_metadata),
            "orchestrator_runtime": {
                "implementation": platform.python_implementation(),
                "python": platform.python_version(),
            },
        }
        try:
            _write_json_exclusive(manifest_path, manifest)
        except OSError as write_exc:
            print(f"error: reproduction failed and manifest write failed: {write_exc}", file=sys.stderr)
            return 2
        print(f"error: {exc}; failure evidence: {manifest_path}", file=sys.stderr)
        return 1

    try:
        _write_json_exclusive(manifest_path, manifest)
    except OSError as exc:
        print(f"error: cannot retain PASS manifest: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
