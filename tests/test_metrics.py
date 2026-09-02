from evidence_inspector.metrics import build_metrics
from evidence_inspector.schemas import (
    ClaimAssessment,
    EvidenceMatch,
    ExpectedClaim,
    Requirement,
    SupportLabel,
)


def _assessment(claim_id: str, label: SupportLabel, requirement_ids: list[str]):
    return ClaimAssessment(
        claim_id=claim_id,
        claim_text="Synthetic claim [E1].",
        label=label,
        confidence=1.0,
        rationale="fixture",
        cited_evidence_ids=["E1"],
        evidence_matches=[EvidenceMatch(evidence_id="E1", score=1.0, excerpt="Synthetic claim")],
        quote_checks=[],
        requirement_ids=requirement_ids,
    )


def test_metrics_score_labels_risk_and_requirement_mapping() -> None:
    assessments = [
        _assessment("c001", SupportLabel.SUPPORTED, ["R1"]),
        _assessment("c002", SupportLabel.UNSUPPORTED, ["R2"]),
    ]
    expected = [
        ExpectedClaim(claim_id="c001", label="SUPPORTED", requirement_ids=["R1"]),
        ExpectedClaim(claim_id="c002", label="UNSUPPORTED", requirement_ids=["R2"]),
    ]
    metrics = build_metrics(
        assessments,
        [Requirement(id="R1", text="First requirement"), Requirement(id="R2", text="Second requirement")],
        expected,
        {"E1"},
    )
    assert metrics.citation_completeness == 1.0
    assert metrics.risky_precision == 1.0
    assert metrics.risky_recall == 1.0
    assert metrics.requirement_mapping_macro_f1 == 1.0

