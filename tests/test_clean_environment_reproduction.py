from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load_script():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_clean_environment_reproduction.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_clean_environment_reproduction", path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_environment_is_minimal_offline_and_drops_credentials() -> None:
    harness = _load_script()
    environment = harness.build_sanitized_environment(
        {
            "HOME": "/safe/home",
            "PATH": "/safe/bin",
            "EVIDENCE_INSPECTOR_MODEL_API_KEY": "must-not-survive",
            "EVIDENCE_INSPECTOR_MODEL_ENDPOINT": "https://provider.example/api",
            "EVIDENCE_INSPECTOR_MODEL_ALLOWED_HOSTS": "provider.example",
            "OPENAI_API_KEY": "must-not-survive-either",
            "UV_INDEX_URL": "https://credentials@example.invalid/simple",
            "HTTPS_PROXY": "http://proxy.example.invalid",
        }
    )

    assert environment["HOME"] == "/safe/home"
    assert environment["PATH"] == "/safe/bin"
    assert environment["EVIDENCE_INSPECTOR_GATEWAY"] == "fixture"
    assert environment["UV_OFFLINE"] == "1"
    assert environment["UV_PYTHON_DOWNLOADS"] == "never"
    assert environment["UV_KEYRING_PROVIDER"] == "disabled"
    assert "EVIDENCE_INSPECTOR_MODEL_API_KEY" not in environment
    assert "EVIDENCE_INSPECTOR_MODEL_ENDPOINT" not in environment
    assert "EVIDENCE_INSPECTOR_MODEL_ALLOWED_HOSTS" not in environment
    assert "OPENAI_API_KEY" not in environment
    assert "UV_INDEX_URL" not in environment
    assert "HTTPS_PROXY" not in environment

    online_install = harness.build_sanitized_environment(
        {"HOME": "/safe/home", "PATH": "/safe/bin", "OPENAI_API_KEY": "drop"},
        allow_dependency_downloads=True,
    )
    assert "UV_OFFLINE" not in online_install
    assert online_install["EVIDENCE_INSPECTOR_GATEWAY"] == "fixture"
    assert "OPENAI_API_KEY" not in online_install


def test_locked_metadata_requires_exact_python_311_contract(tmp_path) -> None:
    harness = _load_script()
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "evidence-inspector"
version = "0.1.0"
requires-python = ">=3.11,<3.12"
[project.optional-dependencies]
dev = ["hatchling==1.31.0"]
[build-system]
requires = ["hatchling==1.31.0"]
build-backend = "hatchling.build"
""".strip(),
        encoding="utf-8",
    )
    lock_path = tmp_path / "uv.lock"
    lock_path.write_text(
        """
version = 1
requires-python = "==3.11.*"
[[package]]
name = "evidence-inspector"
version = "0.1.0"
source = { editable = "." }
[[package]]
name = "hatchling"
version = "1.31.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/aa/hatchling.tar.gz", hash = "sha256:0000000000000000000000000000000000000000000000000000000000000000", size = 1 }
""".strip(),
        encoding="utf-8",
    )

    metadata = harness.validate_locked_metadata(tmp_path)
    assert metadata["project_requires_python"] == ">=3.11,<3.12"
    assert metadata["lock_requires_python"] == "==3.11.*"
    assert metadata["build_requirement"] == "hatchling==1.31.0"
    assert metadata["locked_build_backend_version"] == "1.31.0"

    lock_path.write_text(
        lock_path.read_text(encoding="utf-8").replace("==3.11.*", ">=3.11"),
        encoding="utf-8",
    )
    with pytest.raises(harness.HarnessError, match="must retain requires-python"):
        harness.validate_locked_metadata(tmp_path)

    lock_path.write_text(
        lock_path.read_text(encoding="utf-8").replace(
            'requires-python = ">=3.11"', 'requires-python = "==3.11.*"'
        ).replace('version = "1.31.0"', 'version = "1.30.0"'),
        encoding="utf-8",
    )
    with pytest.raises(harness.HarnessError, match="build backend"):
        harness.validate_locked_metadata(tmp_path)


def test_existing_evidence_root_is_refused_without_modification(tmp_path) -> None:
    harness = _load_script()
    root = tmp_path / "retained-evidence"
    root.mkdir()
    sentinel = root / "sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(harness.HarnessError, match="refusing to reuse"):
        harness.prepare_new_run_root(root)
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert list(root.iterdir()) == [sentinel]


def test_snapshot_is_explicit_hash_backed_and_no_clobber(tmp_path) -> None:
    harness = _load_script()
    project_root = Path(__file__).resolve().parents[1]
    checkout = tmp_path / "checkout"

    manifest = harness.copy_snapshot(project_root, checkout)
    paths = {item["path"] for item in manifest}
    assert "uv.lock" in paths
    assert "pyproject.toml" in paths
    assert "examples/sample_bundle.json" in paths
    assert "scripts/check_fixture_reproducibility.py" in paths
    assert "src/evidence_inspector/gateway.py" in paths
    assert all("acceptance/" not in path for path in paths)
    assert all((checkout / item["path"]).is_file() for item in manifest)

    with pytest.raises(FileExistsError):
        harness.copy_snapshot(project_root, checkout)


def test_fixture_evidence_fails_closed_on_external_gateway_or_mismatch() -> None:
    harness = _load_script()
    passing = {
        "status": "PASS",
        "fixture_only": True,
        "external_api_used": False,
        "bundle_id": "sample-audit-001",
        "first_normalized_sha256": "a" * 64,
        "input_artifacts_match": True,
        "input_sha256_match": True,
        "match": True,
        "persisted_artifacts_verified": True,
        "process_isolated": True,
        "second_normalized_sha256": "a" * 64,
    }
    harness.validate_fixture_evidence(passing)

    with pytest.raises(harness.HarnessError, match="failed closed"):
        harness.validate_fixture_evidence({**passing, "external_api_used": True})
    with pytest.raises(harness.HarnessError, match="failed closed"):
        harness.validate_fixture_evidence({**passing, "match": False})
    missing_isolation = dict(passing)
    missing_isolation.pop("process_isolated")
    with pytest.raises(harness.HarnessError, match="failed closed"):
        harness.validate_fixture_evidence(missing_isolation)
