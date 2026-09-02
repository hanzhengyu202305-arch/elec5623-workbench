#!/usr/bin/env python3
"""Render and validate the ELEC5623 proposal candidate PDF.

This builder intentionally produces a visibly blocked draft. It must not be
renamed to the final Canvas filename until the real team and tutor gates close.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import os
import re
import stat
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

try:
    import pdfplumber
    from pypdf import PdfReader
    from pypdf.generic import ContentStream
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        CondPageBreak,
        LongTable,
        PageBreak,
        Paragraph,
        Preformatted,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError as exc:  # pragma: no cover - environment diagnostic
    raise SystemExit(
        "Missing PDF dependency. Run this script with the bundled workspace "
        "Python or install reportlab, pdfplumber, and pypdf.\n"
        f"Import failure: {exc}"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "PROPOSAL_CANDIDATE_NOT_FOR_SUBMISSION.md"
DEFAULT_OUTPUT = (
    ROOT
    / "output"
    / "pdf"
    / "ELEC5623_GroupXX_Proposal_DRAFT_NOT_FOR_SUBMISSION.pdf"
)

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_ITALIC = "/System/Library/Fonts/Supplemental/Arial Italic.ttf"
FONT_BOLD_ITALIC = "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf"

SECTION_RE = re.compile(r"^## ([1-9][0-9]*)\. (.+?)\s*$", re.MULTILINE)
WORD_RE = re.compile(r"[A-Za-z0-9]+")
TABLE_SEPARATOR_RE = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+\s*$")
ASCII_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(?:[^`~]*)$")
H1_RE = re.compile(r"^ {0,3}# (.+?)\s*$")

EXPECTED_H1_LINES = (
    "DRAFT_NOT_FOR_SUBMISSION - DO NOT UPLOAD TO CANVAS",
    "Model Effectiveness Evaluation Workbench",
)
EXPECTED_SECTIONS = (
    (1, "Cover and group information"),
    (2, "Executive summary"),
    (3, "Introduction and background"),
    (4, "Problem statement and motivation"),
    (5, "Stakeholders and requirements engineering"),
    (6, "Proposed product and innovation"),
    (7, "Proposed methodology and system design"),
    (8, "Business and product analysis"),
    (9, "Evaluation plan"),
    (10, "Risks, ethics and responsible AI"),
    (11, "Semester plan and team responsibilities"),
    (12, "References"),
)

# These floors are deliberately candidate-specific. They catch a deleted or
# accidentally truncated section before layout can still look superficially
# valid. Intentional large rewrites require an explicit review of these values.
MIN_SECTION_WORDS = {
    1: 80,
    2: 120,
    3: 150,
    4: 90,
    5: 700,
    6: 120,
    7: 200,
    8: 160,
    9: 500,
    10: 280,
    11: 250,
    12: 140,
}

REQUIRED_MARKERS_BY_SECTION = {
    1: (
        "GroupXX",
        "[REQUIRED: actual Canvas group number]",
        "[REQUIRED: authorised lab tutor name]",
    ),
    5: ("FR-18", "NFR-10", "C-06"),
    9: ("DRAFT_UNFROZEN_NOT_TUTOR_APPROVED",),
    10: ("OpenAI Codex was materially used", "PRIOR_WORK_DISCLOSURE.md"),
    12: ("[7] pytest developers",),
}

MIN_PAGE_SOURCE_TRIGRAMS = 50
MIN_LONG_BLOCK_TRIGRAM_COVERAGE = 0.60


class ProposalPdfError(RuntimeError):
    """Raised when rendering or validation cannot prove a safe draft."""


@dataclass(frozen=True)
class SourceSnapshot:
    """Identity and content handle for the exact Markdown bytes rendered."""

    device: int
    inode: int
    mode: int
    size: int
    modified_ns: int
    changed_ns: int
    sha256: str


def word_tokens(value: str) -> tuple[str, ...]:
    return tuple(token.lower() for token in WORD_RE.findall(value))


def trigrams(tokens: tuple[str, ...]) -> list[tuple[str, str, str]]:
    return list(zip(tokens, tokens[1:], tokens[2:]))


def opening_fence(line: str) -> tuple[str, int] | None:
    match = FENCE_RE.match(line)
    if match is None:
        return None
    marker = match.group(1)
    return marker[0], len(marker)


def closes_fence(line: str, character: str, minimum_length: int) -> bool:
    return bool(
        re.match(
            rf"^ {{0,3}}{re.escape(character)}{{{minimum_length},}}\s*$",
            line,
        )
    )


def source_without_fenced_code(source_text: str) -> str:
    """Mask fenced code while preserving source offsets and line boundaries."""

    masked: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in source_text.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        ending = line[len(stripped) :]
        if fence_character is None:
            opened = opening_fence(stripped)
            if opened:
                fence_character, fence_length = opened
                masked.append(" " * len(stripped) + ending)
            else:
                masked.append(line)
            continue
        closing = closes_fence(stripped, fence_character, fence_length)
        masked.append(" " * len(stripped) + ending)
        if closing:
            fence_character = None
            fence_length = 0
    if fence_character is not None:
        raise ProposalPdfError("Unclosed Markdown code fence")
    return "".join(masked)


def capture_source(source: Path) -> tuple[str, SourceSnapshot]:
    """Read one stable regular file and bind the build to its exact bytes."""

    descriptor = os.open(source, os.O_RDONLY)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ProposalPdfError(f"Source Markdown is not a regular file: {source}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if identity_before != identity_after:
        raise ProposalPdfError(f"Source Markdown changed while being read: {source}")
    source_bytes = b"".join(chunks)
    try:
        source_text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProposalPdfError(f"Source Markdown is not valid UTF-8: {source}") from exc
    snapshot = SourceSnapshot(
        device=after.st_dev,
        inode=after.st_ino,
        mode=after.st_mode,
        size=after.st_size,
        modified_ns=after.st_mtime_ns,
        changed_ns=after.st_ctime_ns,
        sha256=hashlib.sha256(source_bytes).hexdigest(),
    )
    return source_text, snapshot


def ensure_source_unchanged(source: Path, expected: SourceSnapshot) -> None:
    """Re-read the source immediately before publish and require exact identity."""

    _, current = capture_source(source)
    if current != expected:
        raise ProposalPdfError(
            "Source Markdown changed during build; refusing to publish a stale PDF"
        )


def validate_source_structure(source_text: str) -> dict[int, str]:
    """Require the exact candidate skeleton and substantive section bodies."""

    structural_text = source_without_fenced_code(source_text)
    unsupported_indented = [
        line
        for line in structural_text.splitlines()
        if line.strip() and (line.startswith("    ") or line.startswith("\t"))
    ]
    if unsupported_indented:
        raise ProposalPdfError(
            "Indented Markdown code is unsupported; use an explicit fenced code block"
        )
    visible_lines = [
        line
        for line in structural_text.splitlines()
        if line.strip()
    ]
    expected_prefix = tuple(f"# {value}" for value in EXPECTED_H1_LINES)
    actual_prefix = tuple(visible_lines[:2])
    if actual_prefix != expected_prefix:
        raise ProposalPdfError(
            "The first two non-empty, non-code lines must be the exact draft "
            f"banner and project-title H1 lines; found {actual_prefix}"
        )
    h1_lines = tuple(
        match.group(1).strip()
        for line in structural_text.splitlines()
        if (match := H1_RE.match(line)) is not None
    )
    if h1_lines != EXPECTED_H1_LINES:
        raise ProposalPdfError(
            "Expected the exact draft banner and project-title H1 lines; "
            f"found {h1_lines}"
        )

    matches = list(SECTION_RE.finditer(structural_text))
    found = tuple((int(match.group(1)), match.group(2)) for match in matches)
    if found != EXPECTED_SECTIONS:
        raise ProposalPdfError(
            "Expected exact numbered section headings 1..12; "
            f"found {found}"
        )

    sections: dict[int, str] = {}
    for index, match in enumerate(matches):
        number = int(match.group(1))
        end = matches[index + 1].start() if index + 1 < len(matches) else len(structural_text)
        section_text = structural_text[match.start() : end]
        sections[number] = section_text
        word_count = len(word_tokens(structural_text[match.end() : end]))
        minimum = MIN_SECTION_WORDS[number]
        if word_count < minimum:
            raise ProposalPdfError(
                f"Section {number} is truncated: {word_count} words; minimum {minimum}"
            )

    for number, markers in REQUIRED_MARKERS_BY_SECTION.items():
        missing = [marker for marker in markers if marker not in sections[number]]
        if missing:
            raise ProposalPdfError(
                f"Section {number} is missing required markers: {missing}"
            )
    return sections


def source_content_blocks(source_text: str) -> list[str]:
    """Split rendered Markdown into sentence/table-cell/code anchors."""

    blocks: list[str] = []
    paragraph_lines: list[str] = []
    code_lines: list[str] = []
    fence_character: str | None = None
    fence_length = 0

    def add_sentences(value: str) -> None:
        for sentence in re.split(r"(?<=[.!?])\s+", value.strip()):
            if sentence.strip():
                blocks.append(sentence.strip())

    def flush_paragraph() -> None:
        if paragraph_lines:
            add_sentences(" ".join(paragraph_lines))
            paragraph_lines.clear()

    def flush_code() -> None:
        if code_lines:
            add_sentences(" ".join(code_lines))
            code_lines.clear()

    for line in source_text.splitlines():
        stripped = line.strip()
        if fence_character is None:
            opened = opening_fence(line)
            if opened:
                fence_character, fence_length = opened
                flush_paragraph()
                continue
        elif closes_fence(line, fence_character, fence_length):
            flush_paragraph()
            flush_code()
            fence_character = None
            fence_length = 0
            continue
        if fence_character is not None:
            code_lines.append(stripped)
            continue
        if not stripped:
            flush_paragraph()
            continue
        if TABLE_SEPARATOR_RE.match(stripped):
            flush_paragraph()
            continue
        if stripped.startswith("|"):
            flush_paragraph()
            for cell in split_table_row(stripped):
                if cell:
                    add_sentences(cell)
            continue
        if stripped.startswith(("# ", "## ", "### ", "- ", "* ", "> ")):
            flush_paragraph()
            value = re.sub(r"^(?:#{1,3}|[-*>])\s*", "", stripped)
            add_sentences(value)
            continue
        paragraph_lines.append(stripped)

    flush_paragraph()
    if fence_character is not None:
        raise ProposalPdfError("Unclosed Markdown code fence")
    return blocks


def absolute_output_path(path: Path) -> Path:
    """Resolve only the parent so a final symlink remains visible to lstat."""

    expanded = path.expanduser()
    if not expanded.is_absolute():
        expanded = Path.cwd() / expanded
    return expanded.parent.resolve() / expanded.name


def output_snapshot(output: Path) -> os.stat_result | None:
    try:
        snapshot = output.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(snapshot.st_mode):
        raise ProposalPdfError(f"Output path must not be a symlink: {output}")
    if not stat.S_ISREG(snapshot.st_mode):
        raise ProposalPdfError(f"Output path must be a regular file: {output}")
    return snapshot


def ensure_output_unchanged(output: Path, expected: os.stat_result | None) -> None:
    """Fail if the final path appeared or changed while the temporary PDF built."""

    current = output_snapshot(output)
    if expected is None:
        if current is not None:
            raise ProposalPdfError(f"Output path appeared during build: {output}")
        return
    if current is None:
        raise ProposalPdfError(f"Existing output disappeared during build: {output}")
    expected_identity = (
        expected.st_dev,
        expected.st_ino,
        expected.st_mode,
        expected.st_size,
        expected.st_mtime_ns,
    )
    current_identity = (
        current.st_dev,
        current.st_ino,
        current.st_mode,
        current.st_size,
        current.st_mtime_ns,
    )
    if current_identity != expected_identity:
        raise ProposalPdfError(f"Existing output changed identity during build: {output}")


def register_fonts() -> None:
    paths = [FONT_REGULAR, FONT_BOLD, FONT_ITALIC, FONT_BOLD_ITALIC]
    missing = [path for path in paths if not Path(path).is_file()]
    if missing:
        raise ProposalPdfError(f"Required Arial font files are missing: {missing}")
    pdfmetrics.registerFont(TTFont("ProposalArial", FONT_REGULAR))
    pdfmetrics.registerFont(TTFont("ProposalArial-Bold", FONT_BOLD))
    pdfmetrics.registerFont(TTFont("ProposalArial-Italic", FONT_ITALIC))
    pdfmetrics.registerFont(TTFont("ProposalArial-BoldItalic", FONT_BOLD_ITALIC))
    pdfmetrics.registerFontFamily(
        "ProposalArial",
        normal="ProposalArial",
        bold="ProposalArial-Bold",
        italic="ProposalArial-Italic",
        boldItalic="ProposalArial-BoldItalic",
    )


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=base["BodyText"],
        fontName="ProposalArial",
        fontSize=9.2,
        leading=11.75,
        textColor=colors.HexColor("#172033"),
        spaceAfter=3.8,
        alignment=TA_LEFT,
        allowWidows=0,
        allowOrphans=0,
        splitLongWords=True,
    )
    return {
        "body": body,
        "meta": ParagraphStyle(
            "Meta",
            parent=body,
            fontSize=9.35,
            leading=12.0,
            textColor=colors.HexColor("#334155"),
            spaceAfter=4,
        ),
        "draft": ParagraphStyle(
            "DraftBanner",
            parent=body,
            fontName="ProposalArial-Bold",
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#991B1B"),
            backColor=colors.HexColor("#FEE2E2"),
            borderColor=colors.HexColor("#FCA5A5"),
            borderWidth=0.5,
            borderPadding=6,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "title": ParagraphStyle(
            "Title",
            parent=body,
            fontName="ProposalArial-Bold",
            fontSize=23,
            leading=27,
            textColor=colors.HexColor("#0F2F5F"),
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=body,
            fontName="ProposalArial-Bold",
            fontSize=13.5,
            leading=15.9,
            textColor=colors.HexColor("#0F2F5F"),
            spaceBefore=7,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=body,
            fontName="ProposalArial-Bold",
            fontSize=10,
            leading=12.1,
            textColor=colors.HexColor("#1D4E89"),
            spaceBefore=5,
            spaceAfter=2.5,
            keepWithNext=True,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=body,
            leftIndent=9,
            firstLineIndent=-5,
            bulletIndent=1,
            spaceAfter=2,
        ),
        "table": ParagraphStyle(
            "TableCell",
            parent=body,
            fontSize=7.0,
            leading=8.5,
            spaceAfter=0,
            splitLongWords=True,
        ),
        "table_head": ParagraphStyle(
            "TableHead",
            parent=body,
            fontName="ProposalArial-Bold",
            fontSize=7.1,
            leading=8.6,
            textColor=colors.white,
            spaceAfter=0,
            splitLongWords=True,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=body,
            fontName="Courier",
            fontSize=7.5,
            leading=9.1,
            leftIndent=7,
            rightIndent=7,
            borderColor=colors.HexColor("#CBD5E1"),
            borderWidth=0.5,
            borderPadding=5,
            backColor=colors.HexColor("#F8FAFC"),
            spaceBefore=3,
            spaceAfter=5,
        ),
    }


def inline_markup(value: str) -> str:
    value = ASCII_CONTROL_RE.sub("", value.strip())
    value = html.escape(value, quote=False)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", value)
    value = re.sub(
        r"`([^`]+?)`",
        r'<font name="ProposalArial" color="#7F1D1D">\1</font>',
        value,
    )
    return value


def table_widths(column_count: int, available_width: float) -> list[float]:
    ratios = {
        2: [0.27, 0.73],
        3: [0.18, 0.43, 0.39],
        4: [0.18, 0.28, 0.34, 0.20],
    }.get(column_count)
    if ratios is None:
        ratios = [1 / column_count] * column_count
    return [available_width * ratio for ratio in ratios]


def make_table(rows: list[list[str]], available_width: float, sheet: dict[str, ParagraphStyle]):
    if not rows:
        raise ProposalPdfError("Cannot render an empty Markdown table")
    column_count = len(rows[0])
    if any(len(row) != column_count for row in rows):
        raise ProposalPdfError("Markdown table has inconsistent column counts")
    rendered: list[list[Paragraph]] = []
    for row_index, row in enumerate(rows):
        style = sheet["table_head"] if row_index == 0 else sheet["table"]
        rendered.append([Paragraph(inline_markup(cell), style) for cell in row])
    table_class = LongTable if len(rows) > 5 else Table
    table = table_class(
        rendered,
        colWidths=table_widths(column_count, available_width),
        repeatRows=1,
        hAlign="LEFT",
        splitByRow=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#174A7E")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#94A3B8")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 3.2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3.2),
                ("TOPPADDING", (0, 0), (-1, -1), 2.3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.3),
            ]
        )
    )
    return table


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def build_story(source_text: str, available_width: float):
    validate_source_structure(source_text)
    sheet = styles()
    story = []
    lines = source_text.splitlines()
    paragraph_lines: list[str] = []
    code_lines: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    section_numbers: list[int] = []
    inserted_body_break = False
    inserted_reference_break = False

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        text = " ".join(part.strip() for part in paragraph_lines if part.strip())
        paragraph_lines.clear()
        if text:
            story.append(Paragraph(inline_markup(text), sheet["body"]))

    index = 0
    h1_count = 0
    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if fence_character is None:
            opened = opening_fence(line)
            if opened:
                fence_character, fence_length = opened
                flush_paragraph()
                index += 1
                continue
        elif closes_fence(line, fence_character, fence_length):
            flush_paragraph()
            story.append(Preformatted("\n".join(code_lines), sheet["code"]))
            code_lines.clear()
            fence_character = None
            fence_length = 0
            index += 1
            continue
        if fence_character is not None:
            code_lines.append(line)
            index += 1
            continue
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        section_match = SECTION_RE.match(stripped)
        if section_match:
            flush_paragraph()
            number = int(section_match.group(1))
            section_numbers.append(number)
            if number == 2 and not inserted_body_break:
                story.append(PageBreak())
                inserted_body_break = True
            if number == 12 and not inserted_reference_break:
                story.append(PageBreak())
                inserted_reference_break = True
            if number in {5, 6, 8, 10, 11}:
                story.append(PageBreak())
            else:
                story.append(CondPageBreak(25 * mm))
            story.append(Paragraph(inline_markup(f"{number}. {section_match.group(2)}"), sheet["h2"]))
            index += 1
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            story.append(CondPageBreak(18 * mm))
            story.append(Paragraph(inline_markup(stripped[4:]), sheet["h3"]))
            index += 1
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            h1_count += 1
            title_text = stripped[2:]
            if h1_count == 1:
                story.append(Paragraph(inline_markup(title_text), sheet["draft"]))
            elif h1_count == 2:
                story.append(Spacer(1, 15 * mm))
                story.append(Paragraph(inline_markup(title_text), sheet["title"]))
                story.append(Spacer(1, 4 * mm))
            else:
                story.append(Paragraph(inline_markup(title_text), sheet["h2"]))
            index += 1
            continue
        if stripped.startswith("|") and index + 1 < len(lines):
            flush_paragraph()
            table_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                current = lines[index].strip()
                if not TABLE_SEPARATOR_RE.match(current):
                    table_lines.append(current)
                index += 1
            rows = [split_table_row(row) for row in table_lines]
            story.append(make_table(rows, available_width, sheet))
            story.append(Spacer(1, 3.5))
            continue
        if stripped.startswith(('- ', '* ')):
            flush_paragraph()
            story.append(
                Paragraph(inline_markup(stripped[2:]), sheet["bullet"], bulletText="-")
            )
            index += 1
            continue
        if stripped.startswith("> "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[2:]), sheet["meta"]))
            index += 1
            continue
        if section_numbers == [] and h1_count >= 2:
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped), sheet["meta"]))
        else:
            paragraph_lines.append(stripped)
        index += 1

    flush_paragraph()
    if fence_character is not None:
        raise ProposalPdfError("Unclosed Markdown code fence")
    if section_numbers != [number for number, _ in EXPECTED_SECTIONS]:
        raise ProposalPdfError(
            f"Expected numbered sections 1..12, found {section_numbers}"
        )
    if not inserted_body_break or not inserted_reference_break:
        raise ProposalPdfError("Could not isolate cover, body, and references")
    return story


def draw_page_chrome(canvas, document, *, cover: bool) -> None:
    page_width, page_height = A4
    canvas.saveState()
    canvas.setTitle("ELEC5623 Model Effectiveness Evaluation Workbench - Draft")
    canvas.setAuthor("Zhengyu Han and unconfirmed ELEC5623 group")
    canvas.setSubject("DRAFT - NOT FOR SUBMISSION")
    if not cover:
        canvas.setStrokeColor(colors.HexColor("#94A3B8"))
        canvas.setLineWidth(0.45)
        canvas.line(14 * mm, page_height - 13 * mm, page_width - 14 * mm, page_height - 13 * mm)
        canvas.setFont("ProposalArial", 7)
        canvas.setFillColor(colors.HexColor("#475569"))
        canvas.drawString(14 * mm, page_height - 10.5 * mm, "ELEC5623 - Model Effectiveness Evaluation Workbench")
        canvas.drawRightString(page_width - 14 * mm, page_height - 10.5 * mm, "GroupXX candidate")
    canvas.setFont("ProposalArial-Bold", 7.3)
    canvas.setFillColor(colors.HexColor("#991B1B"))
    canvas.drawCentredString(page_width / 2, 8.5 * mm, "DRAFT - NOT FOR SUBMISSION")
    canvas.setFont("ProposalArial", 7)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawRightString(page_width - 14 * mm, 8.5 * mm, f"Page {document.page}")
    canvas.setFillColor(colors.HexColor("#F4D4DC"))
    canvas.setFont("ProposalArial-Bold", 28)
    canvas.translate(page_width / 2, page_height / 2)
    canvas.rotate(32)
    canvas.drawCentredString(0, 0, "NOT FOR SUBMISSION")
    canvas.restoreState()


def normalize_source_token_sequence(source_text: str) -> tuple[str, ...]:
    kept: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in source_text.splitlines():
        stripped = line.strip()
        if fence_character is None:
            opened = opening_fence(line)
            if opened:
                fence_character, fence_length = opened
                continue
        elif closes_fence(line, fence_character, fence_length):
            fence_character = None
            fence_length = 0
            continue
        if TABLE_SEPARATOR_RE.match(stripped):
            continue
        kept.append(stripped)
    if fence_character is not None:
        raise ProposalPdfError("Unclosed Markdown code fence")
    return word_tokens(" ".join(kept))


def normalize_source_tokens(source_text: str) -> Counter[str]:
    return Counter(normalize_source_token_sequence(source_text))


def expected_page_chrome_tokens(page_number: int) -> tuple[str, ...]:
    header = ""
    if page_number > 1:
        header = (
            "ELEC5623 - Model Effectiveness Evaluation Workbench "
            "GroupXX candidate "
        )
    return word_tokens(
        header
        + f"DRAFT - NOT FOR SUBMISSION Page {page_number} "
        + "NOT FOR SUBMISSION"
    )


def extracted_content_tokens(page_texts: list[str]) -> tuple[str, ...]:
    """Remove the deterministic page chrome and return source-only PDF tokens."""

    content: list[str] = []
    for page_number, page_text in enumerate(page_texts, start=1):
        page_tokens = word_tokens(page_text)
        chrome_tokens = expected_page_chrome_tokens(page_number)
        if page_tokens[: len(chrome_tokens)] != chrome_tokens:
            raise ProposalPdfError(
                "PDF page chrome extraction contract changed on page "
                f"{page_number}; refusing an ambiguous source-content check"
            )
        content.extend(page_tokens[len(chrome_tokens) :])
    return tuple(content)


def reject_invisible_text_rendering(reader: PdfReader) -> None:
    """Reject text rendering modes that can satisfy extraction while drawing nothing."""

    visited: set[tuple[str, int, int] | tuple[str, int]] = set()
    direct_objects: list[object] = []

    def object_key(value, resolved) -> tuple[str, int, int] | tuple[str, int]:
        reference = value if hasattr(value, "idnum") else None
        if reference is None:
            reference = getattr(resolved, "indirect_reference", None)
        if reference is not None:
            return ("indirect", int(reference.idnum), int(reference.generation))
        # Keep direct streams alive and assign identity-based stable indices.
        # PageObject.get_contents() may return a temporary ContentStream; using
        # id(resolved) without retaining it lets CPython recycle that address for
        # a later page and incorrectly treat the later stream as already visited.
        for index, direct_object in enumerate(direct_objects):
            if direct_object is resolved:
                return ("direct", index)
        direct_objects.append(resolved)
        return ("direct", len(direct_objects) - 1)

    def inspect(contents, resources, context: str, depth: int = 0) -> None:
        if contents is None:
            return
        if depth > 32:
            raise ProposalPdfError(
                f"PDF form nesting exceeds the fail-closed limit in {context}"
            )
        resolved = contents.get_object() if hasattr(contents, "get_object") else contents
        key = object_key(contents, resolved)
        if key in visited:
            return
        visited.add(key)
        try:
            stream = ContentStream(resolved, reader)
        except Exception as exc:
            raise ProposalPdfError(
                f"Could not decode PDF content stream in {context}"
            ) from exc
        resource_dict = (
            resources.get_object()
            if resources is not None and hasattr(resources, "get_object")
            else resources
        )
        for operands, operator in stream.operations:
            if operator == b"Tr":
                if len(operands) != 1:
                    raise ProposalPdfError(f"Malformed text rendering mode in {context}")
                try:
                    numeric_mode = float(operands[0])
                except (TypeError, ValueError) as exc:
                    raise ProposalPdfError(
                        f"Invalid PDF text rendering mode operand in {context}"
                    ) from exc
                if not numeric_mode.is_integer():
                    raise ProposalPdfError(
                        f"Non-integer PDF text rendering mode {operands[0]} in {context}"
                    )
                mode = int(numeric_mode)
                if mode not in range(8):
                    raise ProposalPdfError(
                        f"Invalid PDF text rendering mode {mode} in {context}"
                    )
                if mode in {3, 7}:
                    raise ProposalPdfError(
                        "Generated PDF contains invisible text rendering mode "
                        f"Tr={mode} in {context}"
                    )
            if operator != b"Do" or not operands or resource_dict is None:
                continue
            xobjects = resource_dict.get("/XObject")
            if xobjects is None:
                continue
            xobject_dict = (
                xobjects.get_object() if hasattr(xobjects, "get_object") else xobjects
            )
            nested = xobject_dict.get(operands[0])
            if nested is None:
                continue
            nested_resolved = (
                nested.get_object() if hasattr(nested, "get_object") else nested
            )
            if nested_resolved.get("/Subtype") != "/Form":
                continue
            nested_resources = nested_resolved.get("/Resources") or resource_dict
            inspect(
                nested,
                nested_resources,
                f"{context} form {operands[0]}",
                depth + 1,
            )

    for page_number, page in enumerate(reader.pages, start=1):
        inspect(page.get_contents(), page.get("/Resources"), f"page {page_number}")


def validate_pdf(pdf_path: Path, source_text: str) -> dict[str, int]:
    validate_source_structure(source_text)
    reader = PdfReader(str(pdf_path))
    if not reader.pages:
        raise ProposalPdfError("Generated PDF has no pages")
    reject_invisible_text_rendering(reader)
    page_texts = [(page.extract_text() or "") for page in reader.pages]
    with pdfplumber.open(str(pdf_path)) as pdf:
        pdfplumber_page_count = len(pdf.pages)
    if pdfplumber_page_count != len(reader.pages):
        raise ProposalPdfError("pypdf/pdfplumber page counts disagree")
    source_token_sequence = word_tokens(source_text)
    source_trigram_set = set(trigrams(source_token_sequence))
    page_source_overlaps: list[int] = []
    for value in page_texts:
        page_trigram_set = set(trigrams(word_tokens(value)))
        page_source_overlaps.append(len(page_trigram_set & source_trigram_set))
    blank_pages = [
        index + 1
        for index, overlap in enumerate(page_source_overlaps)
        if overlap < MIN_PAGE_SOURCE_TRIGRAMS
    ]
    if blank_pages:
        details = {page: page_source_overlaps[page - 1] for page in blank_pages}
        raise ProposalPdfError(
            "Generated PDF contains blank/near-blank content pages; "
            f"source-trigram overlaps={details}, minimum={MIN_PAGE_SOURCE_TRIGRAMS}"
        )

    def find_page(marker: str) -> int:
        matches = [index for index, value in enumerate(page_texts) if marker in value]
        if len(matches) != 1:
            raise ProposalPdfError(f"Expected marker {marker!r} on exactly one page, got {matches}")
        return matches[0]

    section_pages = {
        number: find_page(f"{number}. {title}")
        for number, title in EXPECTED_SECTIONS
    }
    if any(
        section_pages[number] > section_pages[number + 1]
        for number in range(1, 12)
    ):
        raise ProposalPdfError(f"PDF section pages are out of order: {section_pages}")

    body_start = section_pages[2]
    reference_start = section_pages[12]
    if section_pages[1] != 0:
        raise ProposalPdfError("Section 1 must remain on the one-page cover")
    if body_start != 1:
        raise ProposalPdfError(f"Cover must be exactly one page; body starts at index {body_start}")
    body_pages = reference_start - body_start
    if not 8 <= body_pages <= 10:
        raise ProposalPdfError(
            f"Rendered body is {body_pages} pages; required candidate QA range is 8-10"
        )
    if reference_start <= body_start:
        raise ProposalPdfError("References do not follow the body")

    if EXPECTED_H1_LINES[0] not in page_texts[0]:
        raise ProposalPdfError("Draft banner is missing from the cover page")
    if any(EXPECTED_H1_LINES[0] in value for value in page_texts[1:]):
        raise ProposalPdfError("Draft banner must appear only on the cover page")

    combined = "\n".join(page_texts)
    section_positions: dict[int, int] = {}
    for number, title in EXPECTED_SECTIONS:
        marker = f"{number}. {title}"
        positions = [match.start() for match in re.finditer(re.escape(marker), combined)]
        if len(positions) != 1:
            raise ProposalPdfError(
                f"Expected PDF section marker {marker!r} exactly once; got {positions}"
            )
        section_positions[number] = positions[0]
    for number, markers in REQUIRED_MARKERS_BY_SECTION.items():
        end = section_positions.get(number + 1, len(combined))
        section_pdf_text = combined[section_positions[number] : end]
        missing = [marker for marker in markers if marker not in section_pdf_text]
        if missing:
            raise ProposalPdfError(
                f"PDF Section {number} is missing required markers: {missing}"
            )

    pdf_content_token_sequence = extracted_content_tokens(page_texts)
    pdf_token_sequence = pdf_content_token_sequence
    pdf_unigram_set = set(pdf_token_sequence)
    pdf_bigram_set = set(zip(pdf_token_sequence, pdf_token_sequence[1:]))
    pdf_trigram_set = set(trigrams(pdf_token_sequence))
    weak_blocks: list[str] = []
    for block in source_content_blocks(source_text):
        block_tokens = word_tokens(block)
        if not block_tokens:
            continue
        if len(block_tokens) == 1:
            anchors = [block_tokens[0]]
            matches = sum(item in pdf_unigram_set for item in anchors)
        elif len(block_tokens) == 2:
            anchors = [(block_tokens[0], block_tokens[1])]
            matches = sum(item in pdf_bigram_set for item in anchors)
        else:
            anchors = trigrams(block_tokens)
            matches = sum(item in pdf_trigram_set for item in anchors)
        coverage = matches / len(anchors)
        if matches == 0 or (
            len(block_tokens) >= 15
            and coverage < MIN_LONG_BLOCK_TRIGRAM_COVERAGE
        ):
            weak_blocks.append(
                f"{coverage:.1%}: {block[:140]}"
            )
    if weak_blocks:
        raise ProposalPdfError(
            "PDF source-content anchor check failed: " + "; ".join(weak_blocks[:10])
        )

    source_token_sequence = normalize_source_token_sequence(source_text)
    source_token_count = len(source_token_sequence)
    if pdf_content_token_sequence != source_token_sequence:
        mismatch = next(
            (
                index
                for index, (source_token, pdf_token) in enumerate(
                    zip(source_token_sequence, pdf_content_token_sequence)
                )
                if source_token != pdf_token
            ),
            min(len(source_token_sequence), len(pdf_content_token_sequence)),
        )
        source_counts = Counter(source_token_sequence)
        pdf_counts = Counter(pdf_content_token_sequence)
        missing_tokens = source_counts - pdf_counts
        unexpected_tokens = pdf_counts - source_counts
        raise ProposalPdfError(
            "PDF text coverage check failed: "
            f"exact source-token sequence diverges at index {mismatch}; "
            f"source={source_token_sequence[mismatch:mismatch + 8]}, "
            f"pdf={pdf_content_token_sequence[mismatch:mismatch + 8]}, "
            f"missing={missing_tokens.most_common(12)}, "
            f"unexpected={unexpected_tokens.most_common(12)}"
        )
    token_coverage = 1.0

    return {
        "total_pages": len(page_texts),
        "cover_pages": 1,
        "body_pages": body_pages,
        "reference_pages": len(page_texts) - reference_start,
        "source_tokens": source_token_count,
        "text_coverage_bps": round(token_coverage * 10_000),
    }


def render(source: Path, output: Path, *, force: bool = False) -> dict[str, int | str]:
    try:
        source = source.expanduser().resolve(strict=True)
    except FileNotFoundError as exc:
        raise ProposalPdfError(f"Source Markdown not found: {source}") from exc
    output = absolute_output_path(output)
    if not source.is_file():
        raise ProposalPdfError(f"Source Markdown is not a regular file: {source}")
    if output.suffix.lower() != ".pdf":
        raise ProposalPdfError(f"Output filename must end in .pdf: {output}")

    initial_output = output_snapshot(output)
    if initial_output is not None and os.path.samefile(source, output):
        raise ProposalPdfError("Source and output resolve to the same file")
    if initial_output is not None and not force:
        raise ProposalPdfError(
            f"Output already exists; pass --force to replace this exact draft: {output}"
        )

    source_text, source_snapshot = capture_source(source)
    validate_source_structure(source_text)
    register_fonts()
    output.parent.mkdir(parents=True, exist_ok=True)
    available_width = A4[0] - 28 * mm
    story = build_story(source_text, available_width)

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.stem}-", suffix=".pdf", dir=output.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        document = SimpleDocTemplate(
            str(temporary),
            pagesize=A4,
            leftMargin=14 * mm,
            rightMargin=14 * mm,
            topMargin=18 * mm,
            bottomMargin=16 * mm,
            title="ELEC5623 Model Effectiveness Evaluation Workbench - Draft",
            author="Zhengyu Han and unconfirmed ELEC5623 group",
            subject="DRAFT - NOT FOR SUBMISSION",
            invariant=1,
        )
        document.build(
            story,
            onFirstPage=lambda canvas, doc: draw_page_chrome(canvas, doc, cover=True),
            onLaterPages=lambda canvas, doc: draw_page_chrome(canvas, doc, cover=False),
        )
        result = validate_pdf(temporary, source_text)
        result["source_sha256"] = source_snapshot.sha256
        ensure_source_unchanged(source, source_snapshot)
        ensure_output_unchanged(output, initial_output)
        if output.exists() and os.path.samefile(source, output):
            raise ProposalPdfError("Source and output became aliases during build")
        if initial_output is None:
            try:
                os.link(temporary, output)
            except FileExistsError as exc:
                raise ProposalPdfError(
                    f"Output path appeared during atomic publish: {output}"
                ) from exc
            temporary.unlink()
        else:
            os.replace(temporary, output)
        return result
    finally:
        if temporary.exists():
            temporary.unlink()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace one existing regular draft PDF after identity checks",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        source = args.source.expanduser().resolve(strict=True)
        output = absolute_output_path(args.output)
        result = render(source, output, force=args.force)
    except (OSError, ProposalPdfError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "PASS: rendered validated draft "
        f"{output} | total={result['total_pages']} "
        f"cover={result['cover_pages']} body={result['body_pages']} "
        f"references={result['reference_pages']} "
        f"source_tokens={result['source_tokens']} "
        f"text_coverage={result['text_coverage_bps'] / 100:.2f}% "
        f"source_sha256={result['source_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
