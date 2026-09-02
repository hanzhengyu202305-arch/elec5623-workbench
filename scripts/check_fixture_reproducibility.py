#!/usr/bin/env python3
"""Create no-clobber evidence for deterministic fixture-mode reports.

The two evaluations use separate artifact roots.  Only fields that are
expected to vary between otherwise identical executions are removed before
the reports are serialized and hashed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from pydantic import ValidationError

from evidence_inspector.schemas import EvaluationBundle, RunReport


NORMALIZATION_EXCLUDED_FIELDS = ("created_at", "run_id")
ISOLATED_EVALUATION_TIMEOUT_SECONDS = 120.0
_ISOLATED_EVALUATION_PROGRAM = """
import sys
from pathlib import Path

from evidence_inspector.engine import EvaluationService
from evidence_inspector.gateway import FixtureModelGateway
from evidence_inspector.schemas import EvaluationBundle

bundle = EvaluationBundle.model_validate_json(sys.stdin.read())
report = EvaluationService(
    runs_dir=Path(sys.argv[1]),
    gateway=FixtureModelGateway(),
).evaluate(bundle)
sys.stdout.write(report.model_dump_json())
"""


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def normalized_report_bytes(report: RunReport) -> bytes:
    """Return the canonical report bytes used for reproducibility comparison."""

    payload = report.model_dump(mode="json")
    for field in NORMALIZATION_EXCLUDED_FIELDS:
        payload.pop(field)
    return _canonical_json(payload)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def compare_reports(first: RunReport, second: RunReport) -> dict[str, Any]:
    first_bytes = normalized_report_bytes(first)
    second_bytes = normalized_report_bytes(second)
    first_hash = _sha256(first_bytes)
    second_hash = _sha256(second_bytes)
    return {
        "match": first_bytes == second_bytes,
        "first_normalized_sha256": first_hash,
        "second_normalized_sha256": second_hash,
        "normalization_excluded_fields": list(NORMALIZATION_EXCLUDED_FIELDS),
    }


def _run_isolated_evaluation(bundle: EvaluationBundle, artifact_root: Path) -> str:
    """Run one fixture evaluation in a fresh interpreter and return its run id."""

    environment = os.environ.copy()
    environment["EVIDENCE_INSPECTOR_GATEWAY"] = "fixture"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        completed = subprocess.run(
            [sys.executable, "-c", _ISOLATED_EVALUATION_PROGRAM, str(artifact_root)],
            input=bundle.model_dump_json(),
            text=True,
            capture_output=True,
            check=False,
            timeout=ISOLATED_EVALUATION_TIMEOUT_SECONDS,
            env=environment,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("isolated fixture evaluation timed out") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip()[:1000] or "no stderr"
        raise RuntimeError(
            f"isolated fixture evaluation exited {completed.returncode}: {detail}"
        )
    try:
        returned_report = RunReport.model_validate_json(completed.stdout)
    except ValidationError as exc:
        raise RuntimeError("isolated fixture evaluation returned an invalid report") from exc
    return returned_report.run_id


def _read_persisted_run(
    artifact_root: Path,
    run_id: str,
) -> tuple[RunReport, EvaluationBundle, Path, Path]:
    run_dir = artifact_root / run_id
    report_path = run_dir / "report.json"
    input_path = run_dir / "input.bundle.json"
    if not report_path.is_file() or not input_path.is_file():
        raise FileNotFoundError(f"persisted run artifacts are incomplete: {run_dir}")
    report = RunReport.model_validate_json(report_path.read_text(encoding="utf-8"))
    persisted_bundle = EvaluationBundle.model_validate_json(
        input_path.read_text(encoding="utf-8")
    )
    if report.run_id != run_id:
        raise ValueError(f"persisted report run id does not match directory: {run_dir}")
    return report, persisted_bundle, report_path, input_path


def execute_check(bundle: EvaluationBundle, runs_root: Path) -> dict[str, Any]:
    """Evaluate in two processes, then compare schema-validated disk artifacts."""

    if runs_root.exists():
        raise FileExistsError(f"refusing to reuse runs root: {runs_root}")

    first_root = runs_root / "first"
    second_root = runs_root / "second"
    first_run_id = _run_isolated_evaluation(bundle, first_root)
    second_run_id = _run_isolated_evaluation(bundle, second_root)
    first, first_input, first_report_path, first_input_path = _read_persisted_run(
        first_root,
        first_run_id,
    )
    second, second_input, second_report_path, second_input_path = _read_persisted_run(
        second_root,
        second_run_id,
    )
    comparison = compare_reports(first, second)
    expected_input_bytes = _canonical_json(bundle.model_dump(mode="json"))
    first_input_bytes = _canonical_json(first_input.model_dump(mode="json"))
    second_input_bytes = _canonical_json(second_input.model_dump(mode="json"))
    expected_input_hash = _sha256(expected_input_bytes)
    input_artifacts_match = (
        first_input_bytes == second_input_bytes == expected_input_bytes
    )
    report_input_hashes_match = (
        first.input_sha256 == second.input_sha256 == expected_input_hash
    )
    passed = comparison["match"] and input_artifacts_match and report_input_hashes_match
    return {
        "schema_version": "1.0",
        "status": "PASS" if passed else "FAIL",
        "generated_at": datetime.now(UTC).isoformat(),
        "fixture_only": True,
        "external_api_used": False,
        "process_isolated": True,
        "persisted_artifacts_verified": True,
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "bundle_id": bundle.bundle_id,
        "input_sha256": expected_input_hash,
        "input_sha256_match": report_input_hashes_match,
        "input_artifacts_match": input_artifacts_match,
        "first": {
            "run_id": first.run_id,
            "artifact_root": str(first_root.resolve()),
            "report_json_sha256": _sha256(first_report_path.read_bytes()),
            "input_bundle_json_sha256": _sha256(first_input_path.read_bytes()),
        },
        "second": {
            "run_id": second.run_id,
            "artifact_root": str(second_root.resolve()),
            "report_json_sha256": _sha256(second_report_path.read_bytes()),
            "input_bundle_json_sha256": _sha256(second_input_path.read_bytes()),
        },
        **comparison,
    }


def write_evidence(path: Path, evidence: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(evidence, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run two fixture-only evaluations and compare normalized reports."
    )
    parser.add_argument("bundle", type=Path, help="input bundle JSON")
    parser.add_argument(
        "--runs-root",
        type=Path,
        required=True,
        help="new directory under which first/ and second/ artifacts are retained",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="new JSON evidence file; existing files are never overwritten",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.out.exists():
            raise FileExistsError(f"refusing to overwrite evidence report: {args.out}")
        bundle = EvaluationBundle.model_validate_json(args.bundle.read_text(encoding="utf-8"))
        evidence = execute_check(bundle, args.runs_root)
        write_evidence(args.out, evidence)
    except (FileExistsError, OSError, RuntimeError, ValidationError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if evidence["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
