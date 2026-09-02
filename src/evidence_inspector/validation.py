"""Citation, quotation, and untrusted-input validation."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

from .errors import UnsafeInputError
from .schemas import Claim, EvidenceItem, QuoteCheck


_CITATION = re.compile(r"\[(?:evidence:)?([A-Za-z0-9][A-Za-z0-9_.-]{0,63})\]", re.IGNORECASE)
_QUOTE = re.compile(r"[\"“]([^\"”\n]{3,})[\"”]")
_INJECTION_PATTERNS = (
    re.compile(r"\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?\b", re.IGNORECASE),
    re.compile(r"\bsystem\s+prompt\b", re.IGNORECASE),
    re.compile(r"\breveal\s+(?:the\s+)?(?:hidden|developer)\s+(?:prompt|instructions?)\b", re.IGNORECASE),
    re.compile(r"\bact\s+as\s+(?:the\s+)?system\b", re.IGNORECASE),
)


def guard_untrusted_text(fields: Iterable[tuple[str, str]]) -> None:
    for field_name, text in fields:
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(text):
                raise UnsafeInputError(f"prompt-injection pattern detected in {field_name}")


def cited_evidence_ids(claim: Claim) -> list[str]:
    return list(dict.fromkeys(match.group(1) for match in _CITATION.finditer(claim.text)))


def validate_exact_quotes(
    claim: Claim,
    cited_ids: Sequence[str],
    evidence: Sequence[EvidenceItem],
) -> list[QuoteCheck]:
    evidence_by_id = {item.id: item for item in evidence}
    checks: list[QuoteCheck] = []
    for quote in _QUOTE.findall(claim.text):
        matched_id = next(
            (
                evidence_id
                for evidence_id in cited_ids
                if evidence_id in evidence_by_id and quote in evidence_by_id[evidence_id].content
            ),
            None,
        )
        checks.append(QuoteCheck(quote=quote, evidence_id=matched_id, exact_match=matched_id is not None))
    return checks

