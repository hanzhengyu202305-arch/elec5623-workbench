from __future__ import annotations

from pathlib import Path

from evidence_inspector.engine import EvaluationService
from evidence_inspector.schemas import EvaluationBundle, SupportLabel

DAILY = Path(__file__).resolve().parents[1] / "examples" / "daily_lab_writeup.json"


def test_daily_lab_writeup_exposes_the_interesting_failures(tmp_path) -> None:
    bundle = EvaluationBundle.model_validate_json(DAILY.read_text(encoding="utf-8"))
    report = EvaluationService(tmp_path).evaluate(bundle)
    by_id = {item.claim_id: item for item in report.assessments}

    assert by_id["c001"].label is SupportLabel.SUPPORTED
    assert by_id["c003"].label is SupportLabel.PARTIALLY_SUPPORTED
    assert by_id["c004"].label is SupportLabel.CONTRADICTED
    assert by_id["c005"].label is SupportLabel.UNSUPPORTED
    assert "quoted span is not exact" in by_id["c005"].rationale
    assert by_id["c006"].label is SupportLabel.UNSUPPORTED
    assert "E-datasheet" in by_id["c006"].rationale
    assert by_id["c007"].label is SupportLabel.INSUFFICIENT_EVIDENCE
    markdown = (tmp_path / report.run_id / "report.md").read_text(encoding="utf-8")
    assert "### Quality" in markdown
