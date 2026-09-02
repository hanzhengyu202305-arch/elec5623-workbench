from __future__ import annotations

import pytest
from pydantic import ValidationError

from evidence_inspector.schemas import EvaluationBundle


def test_sample_bundle_is_valid(sample_bundle: EvaluationBundle) -> None:
    assert sample_bundle.bundle_id == "sample-audit-001"
    assert len(sample_bundle.expected_claims) == 11


def test_duplicate_requirement_ids_are_rejected(sample_bundle: EvaluationBundle) -> None:
    data = sample_bundle.model_dump(mode="json")
    data["requirements"].append(data["requirements"][0].copy())
    with pytest.raises(ValidationError, match="requirement ids must be unique"):
        EvaluationBundle.model_validate(data)


def test_duplicate_evidence_ids_are_rejected(sample_bundle: EvaluationBundle) -> None:
    data = sample_bundle.model_dump(mode="json")
    data["evidence"].append(data["evidence"][0].copy())
    with pytest.raises(ValidationError, match="evidence ids must be unique"):
        EvaluationBundle.model_validate(data)


def test_duplicate_expected_claim_ids_are_rejected(sample_bundle: EvaluationBundle) -> None:
    data = sample_bundle.model_dump(mode="json")
    data["expected_claims"].append(data["expected_claims"][0].copy())
    with pytest.raises(ValidationError, match="expected claim ids must be unique"):
        EvaluationBundle.model_validate(data)


def test_unknown_expected_requirement_is_rejected(sample_bundle: EvaluationBundle) -> None:
    data = sample_bundle.model_dump(mode="json")
    data["expected_claims"][0]["requirement_ids"] = ["DOES-NOT-EXIST"]
    with pytest.raises(ValidationError, match="unknown requirements"):
        EvaluationBundle.model_validate(data)


def test_extra_fields_are_rejected(sample_bundle: EvaluationBundle) -> None:
    data = sample_bundle.model_dump(mode="json")
    data["unreviewed_magic"] = True
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        EvaluationBundle.model_validate(data)
