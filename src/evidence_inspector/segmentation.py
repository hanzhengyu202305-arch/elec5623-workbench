"""Deterministic Markdown claim segmentation."""

from __future__ import annotations

import re

from .schemas import Claim


_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'“])")
_LIST_PREFIX = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
_FENCE_OPEN = re.compile(r"^(`{3,}|~{3,})(.*)$")
_SETEXT_UNDERLINE = re.compile(r"^(?:=+|-+)$")


def segment_claims(markdown: str) -> list[Claim]:
    """Split prose and list items into stable, non-empty claim units.

    Headings and fenced-code delimiters are ignored. Claim ids are positional so a
    frozen input has stable ids across machines and model providers.
    """

    units: list[str] = []
    lines = markdown.splitlines()
    fence_char: str | None = None
    fence_length = 0
    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if fence_char is not None:
            if line and set(line) == {fence_char} and len(line) >= fence_length:
                fence_char = None
                fence_length = 0
            continue
        fence = _FENCE_OPEN.match(line)
        if fence:
            marker = fence.group(1)
            fence_char = marker[0]
            fence_length = len(marker)
            continue
        if not line or line.startswith("#") or _SETEXT_UNDERLINE.fullmatch(line):
            continue
        next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
        if not _LIST_PREFIX.match(line) and _SETEXT_UNDERLINE.fullmatch(next_line):
            continue
        line = _LIST_PREFIX.sub("", line).strip()
        for sentence in _SENTENCE_BOUNDARY.split(line):
            sentence = sentence.strip()
            if sentence:
                units.append(sentence)
    return [Claim(id=f"c{index:03d}", text=text) for index, text in enumerate(units, 1)]
