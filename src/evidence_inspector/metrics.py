"""Transparent evaluation metrics without hidden sklearn defaults."""

from __future__ import annotations

from collections import Counter

from .schemas import ClaimAssessment, EvaluationMetrics, ExpectedClaim, Requirement, SupportLabel


def _prf(expected: set[str], actual: set[str]) -> tuple[float, float, float]:
    true_positive = len(expected & actual)
    precision = true_positive / len(actual) if actual else 0.0
    recall = true_positive / len(expected) if expected else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def build_metrics(
    assessments: list[ClaimAssessment],
    requirements: list[Requirement],
    expected_claims: list[ExpectedClaim],
    known_evidence_ids: set[str],
) -> EvaluationMetrics:
    count = len(assessments)
    counts = Counter(item.label for item in assessments)
    classification_counts = {label: counts.get(label, 0) for label in SupportLabel}

    complete_citations = sum(
        bool(item.cited_evidence_ids)
        and all(evidence_id in known_evidence_ids for evidence_id in item.cited_evidence_ids)
        for item in assessments
    )
    citation_completeness = complete_citations / count if count else 0.0
    quote_checks = [check for item in assessments for check in item.quote_checks]
    exact_quote_accuracy = (
        sum(check.exact_match for check in quote_checks) / len(quote_checks) if quote_checks else None
    )
    mapped_requirements = {item for assessment in assessments for item in assessment.requirement_ids}
    requirement_coverage = len(mapped_requirements) / len(requirements) if requirements else 0.0

    macro_f1 = risky_precision = risky_recall = mapping_macro_f1 = None
    if expected_claims:
        per_label: list[float] = []
        for label in SupportLabel:
            expected_ids = {item.claim_id for item in expected_claims if item.label == label}
            actual_ids = {item.claim_id for item in assessments if item.label == label}
            per_label.append(_prf(expected_ids, actual_ids)[2])
        macro_f1 = sum(per_label) / len(per_label)

        risky = {SupportLabel.UNSUPPORTED, SupportLabel.CONTRADICTED}
        expected_risky = {item.claim_id for item in expected_claims if item.label in risky}
        actual_risky = {item.claim_id for item in assessments if item.label in risky}
        risky_precision, risky_recall, _ = _prf(expected_risky, actual_risky)

        per_requirement: list[float] = []
        for requirement in requirements:
            expected_ids = {
                item.claim_id for item in expected_claims if requirement.id in item.requirement_ids
            }
            actual_ids = {
                item.claim_id for item in assessments if requirement.id in item.requirement_ids
            }
            per_requirement.append(_prf(expected_ids, actual_ids)[2])
        mapping_macro_f1 = sum(per_requirement) / len(per_requirement) if per_requirement else None

        # Expected ids absent from actual output remain false negatives through
        # the expected sets above; unknown actual ids remain false positives.

    return EvaluationMetrics(
        claim_count=count,
        classification_counts=classification_counts,
        citation_completeness=citation_completeness,
        exact_quote_accuracy=exact_quote_accuracy,
        requirement_coverage=requirement_coverage,
        classification_macro_f1=macro_f1,
        risky_precision=risky_precision,
        risky_recall=risky_recall,
        requirement_mapping_macro_f1=mapping_macro_f1,
    )
