"""Local-only evidence and requirement retrieval."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence

from .schemas import Claim, EvidenceItem, EvidenceMatch, Requirement


_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "by",
    "can",
    "could",
    "each",
    "every",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "its",
    "must",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "were",
    "with",
}


def _stems(token: str) -> set[str]:
    if len(token) > 4 and token.endswith("ies"):
        return {token[:-3] + "y"}
    if len(token) > 4 and token.endswith("ed"):
        # Both forms are retained because English silent-e inflection cannot be
        # recovered reliably without a language model (route/routed versus
        # accept/accepted). The small redundant form is deterministic.
        return {token[:-2], token[:-1]} if token[:-1].endswith("e") else {token[:-2]}
    if len(token) > 4 and token.endswith("ing"):
        return {token[:-3]}
    if len(token) > 3 and token.endswith("s"):
        return {token[:-1]}
    return {token}


def tokens(text: str) -> set[str]:
    text = re.sub(r"\[(?:evidence:)?[A-Za-z0-9_.-]+\]", " ", text, flags=re.IGNORECASE)
    return {
        form
        for token in _TOKEN.findall(text)
        if token.lower() not in _STOP_WORDS
        for form in _stems(token.lower())
    }


def lexical_similarity(left: str, right: str) -> float:
    """Return a bounded Sørensen-Dice lexical similarity."""

    left_tokens, right_tokens = tokens(left), tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return 2.0 * len(left_tokens & right_tokens) / (len(left_tokens) + len(right_tokens))


def _best_excerpt(content: str, query: str, limit: int = 280) -> str:
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", content) if part.strip()]
    if not parts:
        return content[:limit]
    best = max(parts, key=lambda part: lexical_similarity(part, query))
    return best if len(best) <= limit else best[: limit - 1].rstrip() + "…"


class EvidenceRetriever:
    """Use TF-IDF when available, with an explicit deterministic fallback."""

    def __init__(self, evidence: Sequence[EvidenceItem]):
        self._evidence = list(evidence)
        self.backend = "lexical-fallback"
        self._vectorizer = None
        self._matrix = None
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer

            vectorizer = TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                stop_words="english",
                norm="l2",
            )
            matrix = vectorizer.fit_transform(item.content for item in self._evidence)
            self._vectorizer = vectorizer
            self._matrix = matrix
            self.backend = "sklearn-tfidf"
        except (ImportError, ValueError):
            # ImportError supports constrained teaching environments. ValueError
            # covers an all-stop-word evidence set without hiding other bugs.
            pass

    def retrieve(self, claim: Claim, top_k: int = 3) -> list[EvidenceMatch]:
        if not self._evidence:
            return []
        if self._vectorizer is not None and self._matrix is not None:
            query = self._vectorizer.transform([claim.text])
            raw_scores = (self._matrix @ query.T).toarray().ravel().tolist()
        else:
            raw_scores = [lexical_similarity(claim.text, item.content) for item in self._evidence]
        ranked = sorted(
            zip(self._evidence, raw_scores, strict=True),
            key=lambda pair: (-pair[1], pair[0].id),
        )[: max(1, top_k)]
        return [
            EvidenceMatch(
                evidence_id=item.id,
                score=max(0.0, min(1.0, float(score))) if math.isfinite(score) else 0.0,
                excerpt=_best_excerpt(item.content, claim.text),
            )
            for item, score in ranked
        ]


def map_requirements(
    claim: Claim,
    requirements: Sequence[Requirement],
    threshold: float = 0.12,
    limit: int = 1,
) -> list[str]:
    requirement_tokens = {item.id: tokens(item.text) for item in requirements}
    document_frequency = {
        token: sum(token in item_tokens for item_tokens in requirement_tokens.values())
        for token in {token for item_tokens in requirement_tokens.values() for token in item_tokens}
    }
    common = {
        token
        for token, frequency in document_frequency.items()
        if frequency > max(1, len(requirements) / 2)
    }
    claim_tokens = tokens(claim.text) - common

    def discriminative_similarity(requirement: Requirement) -> float:
        right = requirement_tokens[requirement.id] - common
        if not claim_tokens or not right:
            return 0.0
        return 2.0 * len(claim_tokens & right) / (len(claim_tokens) + len(right))

    ranked = sorted(
        ((item.id, discriminative_similarity(item)) for item in requirements),
        key=lambda pair: (-pair[1], pair[0]),
    )
    selected = [requirement_id for requirement_id, score in ranked if score >= threshold][:limit]
    if not selected and ranked and ranked[0][1] > 0.0:
        selected = [ranked[0][0]]
    return selected
