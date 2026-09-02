#!/usr/bin/env python3
"""Regression tests for the proposal-only PDF production boundary.

Run with the bundled workspace Python because PDF production dependencies are
deliberately outside the coursework product environment. Test artifacts remain
in the printed temporary directory for audit; this script performs no bulk or
recursive deletion.
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_proposal_pdf as builder  # noqa: E402


SOURCE = ROOT / "PROPOSAL_CANDIDATE_NOT_FOR_SUBMISSION.md"
PDF = ROOT / "output" / "pdf" / "ELEC5623_GroupXX_Proposal_DRAFT_NOT_FOR_SUBMISSION.pdf"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ProposalPdfBuilderRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.work = Path(tempfile.mkdtemp(prefix="elec5623-proposal-builder-tests-"))
        cls.source_text = SOURCE.read_text(encoding="utf-8")
        print(f"retained_test_artifacts={cls.work}")

    def test_rejects_source_output_same_file_without_damage(self) -> None:
        source = self.work / "same-file.pdf"
        source.write_text(self.source_text, encoding="utf-8")
        before = sha256(source)
        with self.assertRaisesRegex(builder.ProposalPdfError, "same file"):
            builder.render(source, source, force=True)
        self.assertEqual(sha256(source), before)

    def test_rejects_output_symlink_without_touching_victim(self) -> None:
        victim = self.work / "symlink-victim.txt"
        victim.write_text("do-not-overwrite", encoding="utf-8")
        output = self.work / "symlink-output.pdf"
        output.symlink_to(victim)
        with self.assertRaisesRegex(builder.ProposalPdfError, "must not be a symlink"):
            builder.render(SOURCE, output, force=True)
        self.assertEqual(victim.read_text(encoding="utf-8"), "do-not-overwrite")
        self.assertTrue(output.is_symlink())

    def test_rejects_hardlink_alias_without_damage(self) -> None:
        source = self.work / "hardlink-source.md"
        source.write_text(self.source_text, encoding="utf-8")
        output = self.work / "hardlink-output.pdf"
        os.link(source, output)
        before = sha256(source)
        with self.assertRaisesRegex(builder.ProposalPdfError, "same file"):
            builder.render(source, output, force=True)
        self.assertEqual(sha256(source), before)

    def test_existing_output_requires_force(self) -> None:
        output = self.work / "existing.pdf"
        output.write_text("existing-authoritative-file", encoding="utf-8")
        before = sha256(output)
        with self.assertRaisesRegex(builder.ProposalPdfError, "pass --force"):
            builder.render(SOURCE, output)
        self.assertEqual(sha256(output), before)

    def test_rejects_non_pdf_output(self) -> None:
        with self.assertRaisesRegex(builder.ProposalPdfError, "must end in .pdf"):
            builder.render(SOURCE, self.work / "wrong-extension.txt")

    def test_requires_exact_cover_banner_even_if_token_exists_elsewhere(self) -> None:
        changed = self.source_text.replace(
            "# DRAFT_NOT_FOR_SUBMISSION - DO NOT UPLOAD TO CANVAS",
            "# Working proposal candidate",
            1,
        )
        changed += "\nDRAFT_NOT_FOR_SUBMISSION\n"
        with self.assertRaisesRegex(builder.ProposalPdfError, "exact draft banner"):
            builder.validate_source_structure(changed)

    def test_rejects_visible_prefix_before_exact_banner(self) -> None:
        changed = "FINAL_APPROVED_FOR_CANVAS\n\n" + self.source_text
        with self.assertRaisesRegex(builder.ProposalPdfError, "first two non-empty"):
            builder.validate_source_structure(changed)

    def test_fenced_h1_lines_cannot_satisfy_cover_structure(self) -> None:
        expected_prefix = (
            "# DRAFT_NOT_FOR_SUBMISSION - DO NOT UPLOAD TO CANVAS\n\n"
            "# Model Effectiveness Evaluation Workbench"
        )
        fenced_prefix = (
            "~~~text\n"
            "# DRAFT_NOT_FOR_SUBMISSION - DO NOT UPLOAD TO CANVAS\n"
            "# Model Effectiveness Evaluation Workbench\n"
            "~~~~"
        )
        changed = self.source_text.replace(expected_prefix, fenced_prefix, 1)
        with self.assertRaisesRegex(builder.ProposalPdfError, "first two non-empty"):
            builder.validate_source_structure(changed)

    def test_indented_h1_lines_cannot_satisfy_cover_structure(self) -> None:
        changed = self.source_text.replace(
            "# DRAFT_NOT_FOR_SUBMISSION - DO NOT UPLOAD TO CANVAS",
            "    # DRAFT_NOT_FOR_SUBMISSION - DO NOT UPLOAD TO CANVAS",
            1,
        )
        with self.assertRaisesRegex(builder.ProposalPdfError, "Indented Markdown code"):
            builder.validate_source_structure(changed)

    def test_fenced_duplicate_h1_is_ignored_by_structure_parser(self) -> None:
        insertion = (
            "# Model Effectiveness Evaluation Workbench\n\n"
            "````text\n"
            "# DRAFT_NOT_FOR_SUBMISSION - DO NOT UPLOAD TO CANVAS\n"
            "# Model Effectiveness Evaluation Workbench\n"
            "```\n"
            "````"
        )
        changed = self.source_text.replace(
            "# Model Effectiveness Evaluation Workbench",
            insertion,
            1,
        )
        builder.validate_source_structure(changed)

    def test_rejects_unclosed_markdown_fence(self) -> None:
        changed = self.source_text + "\n~~~text\n# hidden heading\n"
        with self.assertRaisesRegex(builder.ProposalPdfError, "Unclosed Markdown code fence"):
            builder.validate_source_structure(changed)

    def test_rejects_heading_only_section(self) -> None:
        start = self.source_text.index("## 7. Proposed methodology and system design")
        end = self.source_text.index("## 8. Business and product analysis")
        changed = (
            self.source_text[:start]
            + "## 7. Proposed methodology and system design\n\n"
            + self.source_text[end:]
        )
        with self.assertRaisesRegex(builder.ProposalPdfError, "Section 7 is truncated"):
            builder.validate_source_structure(changed)

    def test_rejects_source_sentence_missing_from_pdf(self) -> None:
        changed = self.source_text + (
            "\nZephyrquartz cobaltnebula embervector frostmatrix glyphsignal "
            "heliocipher iridiumlattice juniperkernel kryptonledger lumenmesh "
            "mirrornode novapacket orbitquorum prismroute quartzschema "
            "radiantrace solsticeunit tundravector umbravalidation vortexword.\n"
        )
        with self.assertRaisesRegex(builder.ProposalPdfError, "source-content anchor"):
            builder.validate_pdf(PDF, changed)

    def test_rejects_five_token_sentence_missing_from_pdf(self) -> None:
        changed = self.source_text + (
            "\nZephyrquartz cobaltnebula embervector frostmatrix glyphsignal.\n"
        )
        with self.assertRaisesRegex(builder.ProposalPdfError, "source-content anchor"):
            builder.validate_pdf(PDF, changed)

    def test_exact_sequence_rejects_one_missing_repeated_source_token(self) -> None:
        reader = PdfReader(str(PDF))
        page_texts = [(page.extract_text() or "") for page in reader.pages]
        pdf_counts = Counter(builder.extracted_content_tokens(page_texts))
        source_counts = builder.normalize_source_tokens(self.source_text)
        token = next(
            value
            for value, count in source_counts.items()
            if len(value) >= 8 and pdf_counts[value] == count
        )
        changed = self.source_text + f"\n{token}.\n"
        with self.assertRaisesRegex(builder.ProposalPdfError, "exact source-token sequence"):
            builder.validate_pdf(PDF, changed)

    def test_rejects_chrome_only_page_inside_body_budget(self) -> None:
        builder.register_fonts()
        chrome = self.work / "chrome-only.pdf"

        class DummyDocument:
            page = 10

        canvas = Canvas(str(chrome), pagesize=A4, invariant=1)
        builder.draw_page_chrome(canvas, DummyDocument(), cover=False)
        canvas.showPage()
        canvas.save()

        output = self.work / "with-chrome-only-page.pdf"
        original = PdfReader(str(PDF))
        inserted = PdfReader(str(chrome))
        writer = PdfWriter()
        for page in original.pages[:-1]:
            writer.add_page(page)
        writer.add_page(inserted.pages[0])
        writer.add_page(original.pages[-1])
        with output.open("wb") as stream:
            writer.write(stream)

        with self.assertRaisesRegex(builder.ProposalPdfError, "blank/near-blank"):
            builder.validate_pdf(output, self.source_text)

    def test_rejects_chrome_page_with_invisible_source_text(self) -> None:
        builder.register_fonts()
        invisible = self.work / "chrome-invisible-source.pdf"

        class DummyDocument:
            page = 10

        canvas = Canvas(str(invisible), pagesize=A4, invariant=1)
        builder.draw_page_chrome(canvas, DummyDocument(), cover=False)
        text_object = canvas.beginText(18, A4[1] - 80)
        text_object.setFont("ProposalArial", 7)
        text_object.setTextRenderMode(3)
        tokens = builder.word_tokens(self.source_text)[:180]
        for index in range(0, len(tokens), 12):
            text_object.textLine(" ".join(tokens[index : index + 12]))
        canvas.drawText(text_object)
        canvas.showPage()
        canvas.save()

        output = self.work / "with-invisible-source-page.pdf"
        original = PdfReader(str(PDF))
        inserted = PdfReader(str(invisible))
        writer = PdfWriter()
        for page in original.pages[:-1]:
            writer.add_page(page)
        writer.add_page(inserted.pages[0])
        writer.add_page(original.pages[-1])
        with output.open("wb") as stream:
            writer.write(stream)

        # Deterministically simulate direct ContentStream identity reuse. The
        # legacy visited-set key resolved id() through this module, so this
        # forces every direct page stream onto one key and reproduces the
        # skipped Tr=3 scan.
        with mock.patch.object(builder, "id", return_value=1, create=True):
            with self.assertRaisesRegex(
                builder.ProposalPdfError,
                "invisible text rendering",
            ):
                builder.validate_pdf(output, self.source_text)

    def test_rejects_invisible_text_in_nested_form_xobject(self) -> None:
        nested_pdf = self.work / "nested-form-invisible.pdf"
        canvas = Canvas(str(nested_pdf), pagesize=A4, invariant=1)
        canvas.beginForm("InvisibleInner")
        text_object = canvas.beginText(20, 20)
        text_object.setFont("Helvetica", 8)
        text_object.setTextRenderMode(7)
        text_object.textLine("hidden nested form text")
        canvas.drawText(text_object)
        canvas.endForm()
        canvas.beginForm("Outer")
        canvas.doForm("InvisibleInner")
        canvas.endForm()
        canvas.doForm("Outer")
        canvas.showPage()
        canvas.save()

        with self.assertRaisesRegex(builder.ProposalPdfError, "Tr=7"):
            builder.reject_invisible_text_rendering(PdfReader(str(nested_pdf)))

    def test_all_visible_text_rendering_modes_pass_operator_scan(self) -> None:
        visible_pdf = self.work / "visible-text-rendering-modes.pdf"
        canvas = Canvas(str(visible_pdf), pagesize=A4, invariant=1)
        for index, mode in enumerate((0, 1, 2, 4, 5, 6)):
            text_object = canvas.beginText(20, A4[1] - 30 - index * 20)
            text_object.setFont("Helvetica", 8)
            text_object.setTextRenderMode(mode)
            text_object.textLine(f"visible mode {mode}")
            canvas.drawText(text_object)
        canvas.showPage()
        canvas.save()

        builder.reject_invisible_text_rendering(PdfReader(str(visible_pdf)))

    def test_atomic_no_clobber_preserves_last_moment_concurrent_output(self) -> None:
        output = self.work / "last-moment-concurrent.pdf"
        authoritative = b"concurrent-authoritative-output"
        real_link = os.link

        def create_destination_then_link(source, destination, *args, **kwargs):
            Path(destination).write_bytes(authoritative)
            return real_link(source, destination, *args, **kwargs)

        with mock.patch.object(
            builder.os,
            "link",
            side_effect=create_destination_then_link,
        ):
            with self.assertRaisesRegex(builder.ProposalPdfError, "atomic publish"):
                builder.render(SOURCE, output)
        self.assertEqual(output.read_bytes(), authoritative)
        self.assertEqual(list(self.work.glob(f".{output.stem}-*.pdf")), [])

    def test_source_change_before_publish_preserves_forced_output(self) -> None:
        source = self.work / "source-mutated-during-build.md"
        source.write_text(self.source_text, encoding="utf-8")
        source_stat = source.stat()
        output = self.work / "forced-output-preserved.pdf"
        authoritative = b"existing-authoritative-output"
        output.write_bytes(authoritative)
        real_validate = builder.validate_pdf

        def validate_then_mutate(pdf_path, captured_text):
            result = real_validate(pdf_path, captured_text)
            mutated = captured_text.replace("Track B", "Track C", 1)
            self.assertEqual(len(mutated.encode()), len(captured_text.encode()))
            source.write_text(mutated, encoding="utf-8")
            os.utime(
                source,
                ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns),
            )
            return result

        with mock.patch.object(
            builder,
            "validate_pdf",
            side_effect=validate_then_mutate,
        ):
            with self.assertRaisesRegex(builder.ProposalPdfError, "changed during build"):
                builder.render(source, output, force=True)
        self.assertEqual(output.read_bytes(), authoritative)
        self.assertEqual(list(self.work.glob(f".{output.stem}-*.pdf")), [])

    def test_invariant_build_is_byte_reproducible_and_force_is_explicit(self) -> None:
        first = self.work / "invariant-first.pdf"
        second = self.work / "invariant-second.pdf"
        first_result = builder.render(SOURCE, first)
        second_result = builder.render(SOURCE, second)
        self.assertEqual(first_result["source_sha256"], sha256(SOURCE))
        self.assertEqual(second_result["source_sha256"], sha256(SOURCE))
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with self.assertRaisesRegex(builder.ProposalPdfError, "pass --force"):
            builder.render(SOURCE, first)
        builder.render(SOURCE, first, force=True)
        self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
