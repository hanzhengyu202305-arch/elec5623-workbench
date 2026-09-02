from __future__ import annotations

from evidence_inspector.engine import EvaluationService
from evidence_inspector.gateway import FixtureModelGateway
from evidence_inspector.schemas import EvaluationBundle, SupportLabel


def test_vertical_slice_writes_traceable_artifacts(tmp_path, sample_bundle: EvaluationBundle) -> None:
    report = EvaluationService(tmp_path).evaluate(sample_bundle)
    run_dir = tmp_path / report.run_id
    assert report.status == "READY_FOR_HUMAN_REVIEW"
    assert report.metrics.claim_count == 11
    assert report.retrieval_backend in {"sklearn-tfidf", "lexical-fallback"}
    assert (run_dir / "input.bundle.json").is_file()
    assert (run_dir / "report.json").is_file()
    assert (run_dir / "report.md").is_file()
    assert EvaluationService(tmp_path).get_report(report.run_id) == report


def test_unknown_citation_fails_closed(tmp_path, sample_bundle: EvaluationBundle) -> None:
    data = sample_bundle.model_dump(mode="json")
    data["generated_output"]["markdown"] = "A claim cites missing evidence [MISSING]."
    data["expected_claims"] = []
    bundle = EvaluationBundle.model_validate(data)
    report = EvaluationService(tmp_path).evaluate(bundle)
    assert report.assessments[0].label == SupportLabel.UNSUPPORTED


def test_positive_label_without_citation_becomes_unsupported(tmp_path, sample_bundle) -> None:
    data = sample_bundle.model_dump(mode="json")
    data["generated_output"]["markdown"] = "Bundle validation rejects duplicate requirement identifiers."
    data["expected_claims"] = []
    report = EvaluationService(tmp_path).evaluate(EvaluationBundle.model_validate(data))
    assert report.assessments[0].label == SupportLabel.UNSUPPORTED


def test_altered_quote_forces_supported_gateway_decision_to_unsupported(
    tmp_path,
    sample_bundle,
) -> None:
    claim_text = 'Human reviews are appended to "reviews.csv" [E-review].'
    data = sample_bundle.model_dump(mode="json")
    data["generated_output"]["markdown"] = claim_text
    data["expected_claims"] = []
    report = EvaluationService(
        tmp_path,
        gateway=FixtureModelGateway(rules={claim_text: SupportLabel.SUPPORTED}),
    ).evaluate(EvaluationBundle.model_validate(data))
    assessment = report.assessments[0]
    assert assessment.quote_checks[0].exact_match is False
    assert assessment.label == SupportLabel.UNSUPPORTED
    assert assessment.confidence == 1.0
    assert assessment.rationale == "At least one quoted span is not exact in the cited evidence."
