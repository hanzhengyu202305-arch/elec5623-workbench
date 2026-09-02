"""Pydantic contracts for input, evaluation, and human review."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Requirement(StrictModel):
    id: Identifier
    text: Annotated[str, Field(min_length=3, max_length=2000)]
    priority: str = Field(default="must", pattern=r"^(must|should|could)$")


class EvidenceItem(StrictModel):
    id: Identifier
    title: Annotated[str, Field(min_length=1, max_length=300)]
    content: Annotated[str, Field(min_length=1, max_length=50_000)]
    source_url: HttpUrl | None = None
    source_type: str = Field(default="synthetic", max_length=80)


class GeneratedOutput(StrictModel):
    markdown: Annotated[str, Field(min_length=1, max_length=100_000)]
    provider: Annotated[str, Field(min_length=1, max_length=100)] = "fixture"
    model: Annotated[str, Field(min_length=1, max_length=100)] = "fixture-v1"


class SupportLabel(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ExpectedClaim(StrictModel):
    claim_id: Identifier
    label: SupportLabel
    requirement_ids: list[Identifier] = Field(default_factory=list)


class EvaluationBundle(StrictModel):
    schema_version: str = Field(default="1.0", pattern=r"^1\.0$")
    bundle_id: Identifier
    title: Annotated[str, Field(min_length=3, max_length=300)]
    requirements: Annotated[list[Requirement], Field(min_length=1, max_length=100)]
    evidence: Annotated[list[EvidenceItem], Field(min_length=1, max_length=500)]
    generated_output: GeneratedOutput
    expected_claims: list[ExpectedClaim] = Field(default_factory=list)

    @model_validator(mode="after")
    def ids_are_unique_and_references_exist(self) -> "EvaluationBundle":
        requirement_ids = [item.id for item in self.requirements]
        evidence_ids = [item.id for item in self.evidence]
        expected_ids = [item.claim_id for item in self.expected_claims]
        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError("requirement ids must be unique")
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence ids must be unique")
        if len(expected_ids) != len(set(expected_ids)):
            raise ValueError("expected claim ids must be unique")
        known_requirements = set(requirement_ids)
        for expected in self.expected_claims:
            unknown = set(expected.requirement_ids) - known_requirements
            if unknown:
                raise ValueError(
                    f"expected claim {expected.claim_id} references unknown requirements: "
                    f"{sorted(unknown)}"
                )
        return self


class Claim(StrictModel):
    id: Identifier
    text: Annotated[str, Field(min_length=1)]


class EvidenceMatch(StrictModel):
    evidence_id: Identifier
    score: float = Field(ge=0.0, le=1.0)
    excerpt: str


class QuoteCheck(StrictModel):
    quote: str
    evidence_id: Identifier | None = None
    exact_match: bool


class ClaimAssessment(StrictModel):
    claim_id: Identifier
    claim_text: str
    label: SupportLabel
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    cited_evidence_ids: list[Identifier]
    evidence_matches: list[EvidenceMatch]
    quote_checks: list[QuoteCheck]
    requirement_ids: list[Identifier]


class EvaluationMetrics(StrictModel):
    claim_count: int = Field(ge=0)
    classification_counts: dict[SupportLabel, int]
    citation_completeness: float = Field(ge=0.0, le=1.0)
    exact_quote_accuracy: float | None = Field(default=None, ge=0.0, le=1.0)
    requirement_coverage: float = Field(ge=0.0, le=1.0)
    classification_macro_f1: float | None = Field(default=None, ge=0.0, le=1.0)
    risky_precision: float | None = Field(default=None, ge=0.0, le=1.0)
    risky_recall: float | None = Field(default=None, ge=0.0, le=1.0)
    requirement_mapping_macro_f1: float | None = Field(default=None, ge=0.0, le=1.0)


class RunReport(StrictModel):
    schema_version: str = "1.0"
    run_id: Identifier
    bundle_id: Identifier
    created_at: datetime
    status: str = Field(pattern=r"^READY_FOR_HUMAN_REVIEW$")
    gateway: str
    retrieval_backend: str
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    assessments: list[ClaimAssessment]
    metrics: EvaluationMetrics


class ReviewDecision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    NEEDS_CHANGES = "NEEDS_CHANGES"


class HumanReviewInput(StrictModel):
    reviewer: Annotated[str, Field(min_length=1, max_length=200)]
    decision: ReviewDecision
    notes: Annotated[str, Field(min_length=1, max_length=10_000)]
    claim_id: Identifier | None = None


class HumanReviewRecord(HumanReviewInput):
    review_id: Identifier
    run_id: Identifier
    reviewed_at: datetime


class ComparedModelResult(StrictModel):
    model_id: Annotated[str, Field(min_length=1, max_length=100)]
    gateway: Annotated[str, Field(min_length=1, max_length=200)]
    run_id: Identifier
    classification_macro_f1: float | None = Field(default=None, ge=0.0, le=1.0)
    risky_recall: float | None = Field(default=None, ge=0.0, le=1.0)
    risky_precision: float | None = Field(default=None, ge=0.0, le=1.0)
    requirement_mapping_macro_f1: float | None = Field(default=None, ge=0.0, le=1.0)
    requirement_coverage: float = Field(ge=0.0, le=1.0)
    elapsed_seconds: float = Field(ge=0.0)
    estimated_cost_usd: float = Field(ge=0.0)


class SelectionResult(StrictModel):
    policy: str = Field(pattern=r"^(min_cost|quality_task_fit)$")
    selected_model_id: Annotated[str, Field(min_length=1, max_length=100)]
    rule: Annotated[str, Field(min_length=1, max_length=2000)]
    matches_annotation_preferred: bool | None = None
    classification_macro_f1: float | None = Field(default=None, ge=0.0, le=1.0)
    risky_recall: float | None = Field(default=None, ge=0.0, le=1.0)


class ComparisonReport(StrictModel):
    schema_version: str = Field(default="1.0", pattern=r"^1\.0$")
    bundle_id: Identifier
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    elapsed_seconds: float = Field(ge=0.0)
    models: Annotated[list[ComparedModelResult], Field(min_length=2, max_length=20)]
    min_cost: SelectionResult
    quality_task_fit: SelectionResult
    label_verification_available: bool
    annotation_preferred_model_id: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    status: str = Field(pattern=r"^READY_FOR_HUMAN_REVIEW$")
