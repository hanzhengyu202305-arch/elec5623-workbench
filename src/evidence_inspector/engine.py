"""Evaluation orchestration with fail-closed provider and artifact boundaries."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .artifacts import ArtifactStore
from .errors import GroundTruthAlignmentError, NoAuditableClaims, TokenBudgetExceeded
from .gateway import FixtureModelGateway, ModelGateway
from .metrics import build_metrics
from .retrieval import EvidenceRetriever, map_requirements
from .schemas import (
    ClaimAssessment,
    Claim,
    EvaluationBundle,
    HumanReviewInput,
    HumanReviewRecord,
    RunReport,
    SupportLabel,
)
from .segmentation import segment_claims
from .validation import cited_evidence_ids, guard_untrusted_text, validate_exact_quotes


@dataclass(frozen=True)
class EngineConfig:
    top_k: int = 3
    max_input_tokens: int = 12_000


def _canonical_bundle(bundle: EvaluationBundle) -> bytes:
    return json.dumps(
        bundle.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def conservative_token_upper_bound(bundle: EvaluationBundle) -> int:
    """Bound possible input tokens by canonical UTF-8 byte count.

    Every tokenizer token must consume at least one input byte. Counting the
    complete canonical bundle therefore deliberately overestimates, rather than
    underestimates, provider-bound tokens—including long strings with no
    whitespace. This is a safety bound, not a tokenizer-specific estimate.
    """

    return len(_canonical_bundle(bundle))


def _candidate_run_id(bundle: EvaluationBundle, digest: str, now: datetime) -> str:
    safe_bundle = re.sub(r"[^A-Za-z0-9_.-]", "-", bundle.bundle_id)[:24]
    return f"{now.strftime('%Y%m%dT%H%M%SZ')}-{safe_bundle}-{digest[:10]}"


class EvaluationService:
    def __init__(
        self,
        runs_dir: Path | str = "runs",
        gateway: ModelGateway | None = None,
        config: EngineConfig | None = None,
    ) -> None:
        self.store = ArtifactStore(runs_dir)
        self.gateway = gateway or FixtureModelGateway()
        self.config = config or EngineConfig()

    def evaluate(self, bundle: EvaluationBundle) -> RunReport:
        claims = self.validate(bundle)
        bundle_bytes = _canonical_bundle(bundle)
        digest = hashlib.sha256(bundle_bytes).hexdigest()
        retriever = EvidenceRetriever(bundle.evidence)
        known_evidence = {item.id for item in bundle.evidence}
        assessments: list[ClaimAssessment] = []

        for claim in claims:
            citations = cited_evidence_ids(claim)
            all_matches = retriever.retrieve(claim, top_k=len(bundle.evidence))
            matches_by_id = {match.evidence_id: match for match in all_matches}
            cited_matches = [matches_by_id[item] for item in citations if item in matches_by_id]
            matches = all_matches[: self.config.top_k]
            for cited_match in cited_matches:
                if cited_match.evidence_id not in {item.evidence_id for item in matches}:
                    matches.append(cited_match)
            gateway_matches = cited_matches + [
                match for match in matches if match.evidence_id not in set(citations)
            ]
            decision = self.gateway.classify(claim, gateway_matches)
            quote_checks = validate_exact_quotes(claim, citations, bundle.evidence)
            unknown_citations = set(citations) - known_evidence
            invalid_quote = any(not check.exact_match for check in quote_checks)
            label = decision.label
            rationale = decision.rationale
            confidence = decision.confidence
            if unknown_citations:
                label = SupportLabel.UNSUPPORTED
                confidence = 1.0
                rationale = f"Unknown evidence citations: {sorted(unknown_citations)}."
            elif invalid_quote:
                label = SupportLabel.UNSUPPORTED
                confidence = 1.0
                rationale = "At least one quoted span is not exact in the cited evidence."
            elif not citations and label in {
                SupportLabel.SUPPORTED,
                SupportLabel.PARTIALLY_SUPPORTED,
            }:
                label = SupportLabel.UNSUPPORTED
                confidence = max(confidence, 0.9)
                rationale = "A positive support decision requires an explicit evidence citation."
            assessments.append(
                ClaimAssessment(
                    claim_id=claim.id,
                    claim_text=claim.text,
                    label=label,
                    confidence=confidence,
                    rationale=rationale,
                    cited_evidence_ids=citations,
                    evidence_matches=matches,
                    quote_checks=quote_checks,
                    requirement_ids=map_requirements(claim, bundle.requirements),
                )
            )

        metrics = build_metrics(
            assessments,
            bundle.requirements,
            bundle.expected_claims,
            known_evidence,
        )
        now = datetime.now(UTC)
        report = RunReport(
            run_id=_candidate_run_id(bundle, digest, now),
            bundle_id=bundle.bundle_id,
            created_at=now,
            status="READY_FOR_HUMAN_REVIEW",
            gateway=self.gateway.name,
            retrieval_backend=retriever.backend,
            input_sha256=digest,
            assessments=assessments,
            metrics=metrics,
        )
        # No directory is created until validation and every provider call has
        # succeeded, so failure modes cannot masquerade as completed runs.
        return self.store.write_run(bundle, report)

    def get_report(self, run_id: str) -> RunReport:
        return self.store.read_report(run_id)

    def review(self, run_id: str, review: HumanReviewInput) -> HumanReviewRecord:
        return self.store.append_review(run_id, review)

    def validate(self, bundle: EvaluationBundle) -> list[Claim]:
        """Run every provider-free semantic check without creating artifacts."""

        self._preflight(bundle)
        claims = segment_claims(bundle.generated_output.markdown)
        if not claims:
            raise NoAuditableClaims(
                "generated output contains no auditable prose or list-item claims"
            )
        self._validate_ground_truth_alignment(bundle, claims)
        return claims

    def _preflight(self, bundle: EvaluationBundle) -> None:
        upper_bound = conservative_token_upper_bound(bundle)
        if upper_bound > self.config.max_input_tokens:
            raise TokenBudgetExceeded(
                f"conservative token upper bound {upper_bound} exceeds budget "
                f"{self.config.max_input_tokens}"
            )
        guard_untrusted_text(
            [
                *((f"requirements[{item.id}]", item.text) for item in bundle.requirements),
                *((f"evidence[{item.id}]", item.content) for item in bundle.evidence),
                ("generated_output.markdown", bundle.generated_output.markdown),
            ]
        )

    @staticmethod
    def _validate_ground_truth_alignment(
        bundle: EvaluationBundle,
        claims: list[Claim],
    ) -> None:
        if not bundle.expected_claims:
            return
        segmented_ids = {claim.id for claim in claims}
        expected_ids = {expected.claim_id for expected in bundle.expected_claims}
        unannotated = sorted(segmented_ids - expected_ids)
        unknown = sorted(expected_ids - segmented_ids)
        if unannotated or unknown:
            raise GroundTruthAlignmentError(
                "ground truth must cover every segmented claim exactly; "
                f"unannotated segmented claim ids: {unannotated}; "
                f"unknown expected claim ids: {unknown}"
            )
