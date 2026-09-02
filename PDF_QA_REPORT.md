# ELEC5623 Proposal Candidate PDF QA Report

Verified: `2026-09-02` (Australia/Sydney)

Status: `DRAFT_NOT_FOR_SUBMISSION / LAYOUT_PASS / EXTERNAL_GATES_OPEN`

This report covers the blocked proposal candidate only. It is not tutor approval,
member sign-off, or Canvas submission evidence.

## Truth surfaces

| Artifact | SHA-256 |
|---|---|
| `PROPOSAL_CANDIDATE_NOT_FOR_SUBMISSION.md` | `d3f2951610873c9e3876eed29db1cede9c0d2ac92865f0e344a19e8f678bddf6` |
| `scripts/build_proposal_pdf.py` | `a120b09429e2ef46765bb75ff1584ef534a08fa2cb1188cfad3ff43d062b3730` |
| `scripts/test_proposal_pdf_builder.py` | `2f97fd58d86e2721cf438889f6e6b37b461e1b139cb4ffcf071a0b8ca8943917` |
| `output/pdf/ELEC5623_GroupXX_Proposal_DRAFT_NOT_FOR_SUBMISSION.pdf` | `b02f49d538474f22508af731e8ff6558c55e260028c2890f014575506031fab4` |

The builder normalizes `5,328` source tokens across the complete candidate.
Page count, not Markdown word count, controls candidate layout QA.

## Reproduction

This Workbench rebuild used the project `.venv` Python 3.11, which currently
carries the isolated PDF tooling:

```bash
.venv/bin/python scripts/build_proposal_pdf.py --force
```

The builder is no-clobber by default. `--force` is required to replace the one
existing regular blocked draft. Source/output aliases, hard links, final
symlinks, non-PDF suffixes, and an output identity change during the build are
rejected. It captures the source identity and SHA-256 from one stable file
descriptor and rechecks both immediately before publication. An absent output
is published with a same-directory atomic hard-link operation that cannot
replace a last-moment concurrent file; an explicitly forced existing regular
draft is atomically replaced only after validation and identity checks. A
failed build leaves the prior authoritative output unchanged.

The dedicated boundary regression command is:

```bash
.venv/bin/python scripts/test_proposal_pdf_builder.py
```

## Automated result

```text
PASS: total=10 cover=1 body=8 references=1
source_tokens=5328
extracted text coverage=100.00%
builder boundary regressions=22/22 PASS on the current source/PDF
captured source SHA-256=d3f2951610873c9e3876eed29db1cede9c0d2ac92865f0e344a19e8f678bddf6
```

Automated gates verify:

- exact draft-banner/title H1s as the first two non-empty, non-code lines and
  numbered Sections 1-12 with expected titles; fenced or indented headings
  cannot satisfy the structure contract;
- candidate-specific minimum content for every section;
- cover is exactly one page;
- Sections 2-11 occupy 8-10 rendered pages;
- Section 12 starts on a reference-only page;
- no page with fewer than 50 distinct source-content trigrams;
- one-token, two-token and longer sentence/table-cell source anchors remain
  present, including a 60% trigram floor for longer blocks;
- draft, `GroupXX`, `[REQUIRED: ...]`, direct Codex disclosure, frozen-result
  boundary, FR/NFR/constraint, and final-reference sentinels remain in their
  required cover or section rather than anywhere in the file;
- pypdf and pdfplumber agree on page count;
- reachable page/Form content streams contain no invisible `Tr=3` or `Tr=7`
  text rendering mode; direct temporary content streams are retained during
  this scan so recycled CPython object identities cannot skip a later page; and
- after removing the deterministic header/footer/watermark token prefix from
  each page, the complete pypdf token sequence exactly equals all `5,328`
  normalized source tokens. Full raster inspection remains mandatory because
  content-stream checks alone do not prove visual legibility.

## Full visual inspection

After the 2026-09-02 Workbench retitle, all ten pages were rebuilt, rendered at
120 DPI with Poppler, and inspected. Cover title is **Model Effectiveness
Evaluation Workbench**. FR-01 to FR-18 and NFR-10 are visible. `GroupXX` and
approval sentinels remain. Constantinople / ESIPS Pound for Pound is not
claimed complete. A later same-day numeric rebuild (152 tests / 94.02%
coverage) kept 1 cover + 8 body + 1 references with 100% token coverage and
builder regressions 22/22; that numeric rebuild did not repeat the 120-DPI
page-by-page visual pass.

| Page | Classification | Visual result |
|---:|---|---|
| 1 | Cover | PASS - Workbench title, status banner, blocking cover fields, vision and approval warning are visible; no clipping. |
| 2 | Body 1/8 | PASS - Sections 2-4 remain readable; Inspector engine vs Workbench compare shell, min-cost vs quality/task-fit, and no auto-deploy wording are visible. |
| 3 | Body 2/8 | PASS - stakeholder/scope text and complete FR-01 to FR-18 table plus compare CLI are legible; no split or clipped row. |
| 4 | Body 3/8 | PASS - ten NFRs including NFR-10, six constraints, and requirement-to-evaluation trace including FR-16-18 are complete and readable. |
| 5 | Body 4/8 | PASS - Sections 6-7, editable text workflow and data/model/storage boundary are self-contained. |
| 6 | Body 5/8 | PASS - business comparison and evaluation plan remain readable; named-policy contrast is visible. |
| 7 | Body 6/8 | PASS - failure/reproducibility plan and RQ-to-evidence interpretation table are visible; no clipped table cells. |
| 8 | Body 7/8 | PASS - risks, mitigations and direct GenAI/prior-work disclosure are complete and readable. |
| 9 | Body 8/8 | PASS - timeline reaches the final demonstration; 18 FRs and Slot E FR-13-18 plus tutor/submission gates remain. |
| 10 | References | PASS - all seven references and their URLs/DOIs are readable on a reference-only page. |

Headers, footers, page numbers and the pale `NOT FOR SUBMISSION` watermark are
consistent. The watermark is visible without obscuring prose or tables. No
overlap, black square, broken glyph, unreadable URL, clipped line, or accidental
blank page was observed.

## Submission blockers intentionally retained

- `GroupXX`, member names/SIDs, actual per-person FR allocation and reviewers.
- Tutor name, approval date and approval statement.
- Whole-group agreement and written tutor approval of the Workbench direction.
- Week 3 participation and recorded tutor feedback.
- Stakeholder evidence or an explicit tutor-approved alternative.
- Prior-work decision, final annotation/threshold decision and frozen result.
- Final course-policy AI disclosure reconciliation and member sign-off.
- Final filename, final PDF regeneration, Canvas upload and confirmation.

Any change to source content, fonts, margins, tables, group facts, approval text,
references, or renderer code invalidates the hashes and this visual QA result.
Rebuild, rerun all automated gates, render every page again, and update this
report before treating a later PDF as reviewed.
