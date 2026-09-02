from __future__ import annotations

from pathlib import Path

import pytest

from evidence_inspector.compare import (
    ComparisonService,
    build_named_gateway,
)
from evidence_inspector.engine import conservative_token_upper_bound
from evidence_inspector.errors import CompareIncompleteError
from evidence_inspector.gateway import FixtureModelGateway
from evidence_inspector.schemas import ComparisonReport, EvaluationBundle, SupportLabel
from evidence_inspector.segmentation import segment_claims


def _always_supported(bundle: EvaluationBundle) -> dict[str, SupportLabel]:
    return {
        claim.text: SupportLabel.SUPPORTED
        for claim in segment_claims(bundle.generated_output.markdown)
    }


def _compare_paths(root: Path) -> tuple[Path, Path]:
    return root / "compare.json", root / "compare.md"


def test_two_fixture_variants_write_runs_and_schema_valid_compare(
    tmp_path, sample_bundle: EvaluationBundle
) -> None:
    report = ComparisonService(tmp_path).compare(sample_bundle, ["fixture", "fixture-b"])
    json_path, md_path = _compare_paths(tmp_path)
    assert json_path.is_file()
    assert md_path.is_file()
    loaded = ComparisonReport.model_validate_json(json_path.read_text(encoding="utf-8"))
    assert loaded.bundle_id == sample_bundle.bundle_id
    assert loaded.status == "READY_FOR_HUMAN_REVIEW"
    assert len(loaded.models) == 2
    assert {row.model_id for row in loaded.models} == {"fixture", "fixture-b"}
    for row in loaded.models:
        assert (tmp_path / row.run_id / "report.json").is_file()
    assert report.elapsed_seconds <= 60.0
    assert loaded.label_verification_available is True
    markdown = md_path.read_text(encoding="utf-8")
    assert "READY_FOR_HUMAN_REVIEW" in markdown
    assert "combined into one effectiveness index" in markdown
    assert "not a bill" in markdown


def test_unavailable_gateway_is_fail_closed_without_compare_artifacts(
    tmp_path, sample_bundle: EvaluationBundle
) -> None:
    service = ComparisonService(
        tmp_path,
        gateways={
            "fixture": FixtureModelGateway(name="fixture"),
            "down": FixtureModelGateway(name="fixture-b", fail_mode="unavailable"),
        },
    )
    with pytest.raises(CompareIncompleteError, match="comparison incomplete"):
        service.compare(sample_bundle, ["fixture", "down"])
    json_path, md_path = _compare_paths(tmp_path)
    assert not json_path.exists()
    assert not md_path.exists()
    run_dirs = [path for path in tmp_path.iterdir() if path.is_dir()]
    assert run_dirs, "the successful model may retain its Inspector run directory"
    for run_dir in run_dirs:
        assert not (run_dir / "compare.json").exists()


def test_min_cost_and_quality_select_different_models(
    tmp_path, sample_bundle: EvaluationBundle
) -> None:
    cheap = FixtureModelGateway(name="fixture", rules=_always_supported(sample_bundle))
    gold = build_named_gateway("fixture-b", sample_bundle)
    report = ComparisonService(
        tmp_path,
        gateways={"fixture": cheap, "fixture-b": gold},
    ).compare(sample_bundle, ["fixture", "fixture-b"])
    by_id = {row.model_id: row for row in report.models}
    assert by_id["fixture"].estimated_cost_usd == 0.0
    assert by_id["fixture-b"].estimated_cost_usd > 0.0
    assert by_id["fixture"].risky_recall is not None
    assert by_id["fixture-b"].risky_recall is not None
    assert by_id["fixture"].risky_recall < by_id["fixture-b"].risky_recall
    assert report.min_cost.selected_model_id == "fixture"
    assert report.quality_task_fit.selected_model_id == "fixture-b"
    assert report.annotation_preferred_model_id == "fixture-b"
    assert report.min_cost.matches_annotation_preferred is False
    assert report.quality_task_fit.matches_annotation_preferred is True
    assert report.label_verification_available is True


def test_unlabeled_bundle_compares_without_label_verification(
    tmp_path, sample_bundle: EvaluationBundle
) -> None:
    data = sample_bundle.model_dump(mode="json")
    data["expected_claims"] = []
    unlabeled = EvaluationBundle.model_validate(data)
    report = ComparisonService(tmp_path).compare(unlabeled, ["fixture", "fixture-b"])
    assert report.label_verification_available is False
    assert report.annotation_preferred_model_id is None
    assert report.min_cost.matches_annotation_preferred is None
    assert report.quality_task_fit.matches_annotation_preferred is None
    markdown = (tmp_path / "compare.md").read_text(encoding="utf-8")
    assert "predicts success" not in markdown.lower()
    assert "Label verification is not available" in markdown
    assert "comparison only" in markdown


def test_unknown_list_price_fails_closed_after_runs(
    tmp_path, sample_bundle: EvaluationBundle
) -> None:
    service = ComparisonService(
        tmp_path,
        gateways={
            "fixture": FixtureModelGateway(name="fixture"),
            "mystery": FixtureModelGateway(name="unpublished-gateway"),
        },
    )
    with pytest.raises(CompareIncompleteError, match="no published list price"):
        service.compare(sample_bundle, ["fixture", "mystery"])
    json_path, md_path = _compare_paths(tmp_path)
    assert not json_path.exists()
    assert not md_path.exists()


def test_compare_rejects_too_few_or_duplicate_models(
    tmp_path, sample_bundle: EvaluationBundle
) -> None:
    service = ComparisonService(tmp_path)
    with pytest.raises(CompareIncompleteError, match="at least two"):
        service.compare(sample_bundle, ["fixture"])
    with pytest.raises(CompareIncompleteError, match="unique"):
        service.compare(sample_bundle, ["fixture", "fixture"])
    json_path, md_path = _compare_paths(tmp_path)
    assert not json_path.exists()
    assert not md_path.exists()


def test_token_bound_is_shared_public_function(sample_bundle: EvaluationBundle) -> None:
    assert conservative_token_upper_bound(sample_bundle) >= 1
