from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def _load_script(name: str):
    path = Path(__file__).resolve().parents[1] / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_baseline_ablation_and_error_study_is_honest_and_reproducible(tmp_path) -> None:
    generator = _load_script("generate_synthetic_corpus.py")
    study = _load_script("run_baseline_study.py")
    bundles = generator.build_corpus()

    report = study.execute_study(bundles, tmp_path / "runs")

    assert report["status"] == "PASS"
    assert report["study_status"] == "DRAFT_DEV_UNFROZEN_NOT_TUTOR_APPROVED"
    assert report["tutor_approval_claimed"] is False
    assert report["external_api_used"] is False
    assert report["counts"] == {
        "bundles": 20,
        "claims": 200,
        "template_families": 5,
        "markdown_layouts": 4,
    }
    assert report["checks"]["full_replay_matches_service"] is True
    full = report["variants"]["full_fixture_replay"]
    assert report["service_prediction_sha256"] == full["prediction_sha256"]
    assert full["error_count"] > 0
    assert full["label_error_count"] > 0
    assert full["mapping_error_count"] > 0
    assert full["metrics"]["classification_macro_f1"] >= 0.65
    assert full["metrics"]["risky_precision"] >= 0.80
    assert full["metrics"]["risky_recall"] >= 0.75
    assert full["metrics"]["requirement_mapping_macro_f1"] >= 0.70

    baseline = report["variants"]["citation_presence_b0"]
    assert baseline["metrics"]["classification_macro_f1"] < full["metrics"][
        "classification_macro_f1"
    ]
    assert baseline["metrics"]["risky_recall"] == 0.0
    assert baseline["metrics"]["requirement_mapping_macro_f1"] == 0.0

    no_priority = report["variants"]["ablation_no_citation_priority"]
    no_quote = report["variants"]["ablation_no_exact_quote_guard"]
    no_mapping = report["variants"]["ablation_no_requirement_mapping"]
    assert no_priority["prediction_sha256"] != full["prediction_sha256"]
    assert no_priority["metrics"]["risky_precision"] < full["metrics"][
        "risky_precision"
    ]
    assert no_quote["prediction_sha256"] != full["prediction_sha256"]
    assert no_quote["metrics"]["risky_recall"] < full["metrics"]["risky_recall"]
    assert no_mapping["metrics"]["requirement_mapping_macro_f1"] == 0.0

    repeated_rows = study._variant_rows(bundles)
    assert study._canonical_sha256(study._prediction_payload(repeated_rows)) == full[
        "prediction_sha256"
    ]


def test_baseline_study_report_is_no_clobber(tmp_path) -> None:
    study = _load_script("run_baseline_study.py")
    path = tmp_path / "study.json"
    study.write_report(path, {"status": "PASS"})
    assert json.loads(path.read_text(encoding="utf-8")) == {"status": "PASS"}
    with pytest.raises(FileExistsError):
        study.write_report(path, {"status": "FAIL"})


def test_baseline_cli_refuses_existing_runs_root_before_evaluation(
    tmp_path, capsys
) -> None:
    study = _load_script("run_baseline_study.py")
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    output = tmp_path / "study.json"

    exit_code = study.main(
        ["--runs-dir", str(runs_dir), "--out", str(output)]
    )

    assert exit_code == 2
    assert "refusing to reuse" in capsys.readouterr().err
    assert not output.exists()
