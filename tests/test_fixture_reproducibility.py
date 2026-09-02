from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def _load_script():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "check_fixture_reproducibility.py"
    )
    spec = importlib.util.spec_from_file_location("check_fixture_reproducibility", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_two_fixture_runs_have_identical_normalized_reports(tmp_path, sample_bundle) -> None:
    checker = _load_script()
    evidence = checker.execute_check(sample_bundle, tmp_path / "runs")

    assert evidence["status"] == "PASS"
    assert evidence["fixture_only"] is True
    assert evidence["external_api_used"] is False
    assert evidence["process_isolated"] is True
    assert evidence["persisted_artifacts_verified"] is True
    assert evidence["input_sha256_match"] is True
    assert evidence["input_artifacts_match"] is True
    assert evidence["match"] is True
    assert evidence["first_normalized_sha256"] == evidence["second_normalized_sha256"]
    assert evidence["normalization_excluded_fields"] == ["created_at", "run_id"]
    assert (Path(evidence["first"]["artifact_root"]) / evidence["first"]["run_id"] / "report.json").is_file()
    assert (Path(evidence["second"]["artifact_root"]) / evidence["second"]["run_id"] / "report.json").is_file()


def test_check_fails_when_a_persisted_report_changes(
    tmp_path,
    sample_bundle,
    monkeypatch,
) -> None:
    checker = _load_script()
    real_run = checker._run_isolated_evaluation

    def run_then_change_second_report(bundle, artifact_root):
        run_id = real_run(bundle, artifact_root)
        if artifact_root.name == "second":
            from evidence_inspector.schemas import RunReport

            report_path = artifact_root / run_id / "report.json"
            report = RunReport.model_validate_json(report_path.read_text(encoding="utf-8"))
            changed = report.model_copy(update={"retrieval_backend": "persisted-change"})
            report_path.write_text(changed.model_dump_json(indent=2) + "\n", encoding="utf-8")
        return run_id

    monkeypatch.setattr(
        checker,
        "_run_isolated_evaluation",
        run_then_change_second_report,
    )

    evidence = checker.execute_check(sample_bundle, tmp_path / "runs")
    assert evidence["status"] == "FAIL"
    assert evidence["match"] is False
    assert evidence["persisted_artifacts_verified"] is True


def test_check_refuses_to_pass_when_runner_returns_phantom_artifacts(
    tmp_path,
    sample_bundle,
    monkeypatch,
) -> None:
    checker = _load_script()
    monkeypatch.setattr(
        checker,
        "_run_isolated_evaluation",
        lambda bundle, artifact_root: "phantom-run",
    )

    with pytest.raises(FileNotFoundError, match="persisted run artifacts are incomplete"):
        checker.execute_check(sample_bundle, tmp_path / "phantom-runs")
    assert not (tmp_path / "phantom-runs").exists()


def test_comparison_detects_a_stable_field_change(tmp_path, sample_bundle) -> None:
    checker = _load_script()
    evidence = checker.execute_check(sample_bundle, tmp_path / "runs")
    first_path = (
        Path(evidence["first"]["artifact_root"])
        / evidence["first"]["run_id"]
        / "report.json"
    )
    second_path = (
        Path(evidence["second"]["artifact_root"])
        / evidence["second"]["run_id"]
        / "report.json"
    )
    from evidence_inspector.schemas import RunReport

    first = RunReport.model_validate_json(first_path.read_text(encoding="utf-8"))
    second = RunReport.model_validate_json(second_path.read_text(encoding="utf-8"))
    changed = second.model_copy(update={"retrieval_backend": "changed-backend"})

    comparison = checker.compare_reports(first, changed)
    assert comparison["match"] is False
    assert comparison["first_normalized_sha256"] != comparison["second_normalized_sha256"]


def test_cli_is_no_clobber_and_writes_evidence(tmp_path, sample_bundle, capsys) -> None:
    checker = _load_script()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(sample_bundle.model_dump_json(indent=2) + "\n", encoding="utf-8")
    runs_root = tmp_path / "runs"
    evidence_path = tmp_path / "evidence.json"
    arguments = [
        str(bundle_path),
        "--runs-root",
        str(runs_root),
        "--out",
        str(evidence_path),
    ]

    assert checker.main(arguments) == 0
    retained = evidence_path.read_bytes()
    assert json.loads(retained)["status"] == "PASS"
    assert checker.main(arguments) == 2
    assert evidence_path.read_bytes() == retained
    assert "refusing to overwrite" in capsys.readouterr().err


def test_existing_runs_root_fails_before_creating_evidence(tmp_path, sample_bundle) -> None:
    checker = _load_script()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(sample_bundle.model_dump_json(indent=2), encoding="utf-8")
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    evidence_path = tmp_path / "evidence.json"

    exit_code = checker.main(
        [
            str(bundle_path),
            "--runs-root",
            str(runs_root),
            "--out",
            str(evidence_path),
        ]
    )
    assert exit_code == 2
    assert not evidence_path.exists()
