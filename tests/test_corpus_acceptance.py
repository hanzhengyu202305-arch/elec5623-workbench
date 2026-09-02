from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from evidence_inspector.schemas import EvaluationBundle


def _load_script(name: str):
    path = Path(__file__).resolve().parents[1] / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_draft_corpus_acceptance_passes_and_is_reproducible(tmp_path) -> None:
    generator = _load_script("generate_synthetic_corpus.py")
    acceptance = _load_script("run_corpus_acceptance.py")
    bundles = generator.build_corpus()
    first = acceptance.execute_acceptance(bundles, tmp_path / "runs-a")
    second = acceptance.execute_acceptance(bundles, tmp_path / "runs-b")
    assert first["status"] == "PASS"
    assert first["corpus_status"] == "DRAFT_UNFROZEN_NOT_TUTOR_APPROVED"
    assert first["tutor_approval_claimed"] is False
    assert first["external_api_used"] is False
    assert first["counts"] == {
        "bundles": 20,
        "expected_claims": 200,
        "evaluated_claims": 200,
    }
    assert first["corpus_sha256"] == second["corpus_sha256"]
    assert first["prediction_sha256"] == second["prediction_sha256"]
    assert all(check["passed"] for check in first["checks"].values())
    assert first["checks"]["elapsed_seconds"]["operator"] == "<="
    assert first["checks"]["elapsed_seconds"]["threshold"] == 60.0
    assert first["elapsed_seconds"] <= 60.0
    assert first["effectiveness"]["combined_index"] is False
    assert first["effectiveness"]["price_used_as_quality"] is False
    assert first["effectiveness"]["predicts"] == "supplied_expected_labels"
    assert first["effectiveness"]["efficiency"]["token_spend_aud"] is None
    assert first["effectiveness"]["quality"]["classification_macro_f1"] == (
        first["metrics"]["classification_macro_f1"]
    )
    assert first["effectiveness"]["task_fit"]["requirement_mapping_macro_f1"] == (
        first["metrics"]["requirement_mapping_macro_f1"]
    )


def test_slow_elapsed_time_fails_acceptance_check() -> None:
    acceptance = _load_script("run_corpus_acceptance.py")
    passing_metrics = {name: threshold for name, threshold in acceptance.THRESHOLDS.items()}
    checks = acceptance.build_checks(passing_metrics, 60.000001)
    assert checks["elapsed_seconds"] == {
        "operator": "<=",
        "threshold": 60.0,
        "actual": 60.000001,
        "passed": False,
    }
    assert not all(check["passed"] for check in checks.values())


def test_acceptance_report_refuses_to_overwrite(tmp_path) -> None:
    acceptance = _load_script("run_corpus_acceptance.py")
    path = tmp_path / "acceptance.json"
    acceptance.write_report(path, {"status": "PASS"})
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "PASS"
    with pytest.raises(FileExistsError):
        acceptance.write_report(path, {"status": "FAIL"})


def test_acceptance_rejects_wrong_corpus_shape(tmp_path) -> None:
    generator = _load_script("generate_synthetic_corpus.py")
    acceptance = _load_script("run_corpus_acceptance.py")
    with pytest.raises(ValueError, match="exactly 20 bundles and 200 expected claims"):
        acceptance.execute_acceptance(generator.build_corpus()[:1], tmp_path / "runs")


def test_duplicate_bundle_ids_fail_before_any_run(tmp_path, capsys) -> None:
    generator = _load_script("generate_synthetic_corpus.py")
    acceptance = _load_script("run_corpus_acceptance.py")
    bundles = generator.build_corpus()
    duplicate_data = bundles[-1].model_dump(mode="json")
    duplicate_data["bundle_id"] = bundles[0].bundle_id
    bundles[-1] = EvaluationBundle.model_validate(duplicate_data)
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    for index, bundle in enumerate(bundles, 1):
        (corpus_dir / f"synthetic-{index:02d}.json").write_text(
            bundle.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
    runs_dir = tmp_path / "runs"
    report_path = tmp_path / "acceptance.json"
    exit_code = acceptance.main(
        [
            "--corpus-dir",
            str(corpus_dir),
            "--runs-dir",
            str(runs_dir),
            "--out",
            str(report_path),
        ]
    )
    assert exit_code == 2
    assert "bundle ids must be globally unique" in capsys.readouterr().err
    assert not runs_dir.exists()
    assert not report_path.exists()


def test_expected_claim_ids_must_align_before_any_run(tmp_path) -> None:
    generator = _load_script("generate_synthetic_corpus.py")
    acceptance = _load_script("run_corpus_acceptance.py")
    bundles = generator.build_corpus()
    mismatched = bundles[0].model_dump(mode="json")
    mismatched["expected_claims"][-1]["claim_id"] = "c999"
    bundles[0] = EvaluationBundle.model_validate(mismatched)
    runs_dir = tmp_path / "runs"
    with pytest.raises(ValueError, match="do not align with segmentation"):
        acceptance.execute_acceptance(bundles, runs_dir)
    assert not runs_dir.exists()
