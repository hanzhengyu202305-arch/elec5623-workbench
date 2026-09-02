from pathlib import Path

from scripts.check_proposal_structure import EXPECTED_SECTIONS, numbered_sections


ROOT = Path(__file__).resolve().parents[1]


def test_proposal_headings_match_captured_brief_order() -> None:
    proposal = (ROOT / "PROPOSAL_DRAFT.md").read_text(encoding="utf-8")

    assert numbered_sections(ROOT / "PROPOSAL_DRAFT.md") == EXPECTED_SECTIONS
    assert "OpenAI Codex was materially used" in proposal
    assert "### 12.3 Required appendices" not in proposal
    assert "permitted appendices" not in proposal
