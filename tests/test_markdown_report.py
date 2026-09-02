from __future__ import annotations

from evidence_inspector.artifacts import render_markdown
from evidence_inspector.engine import EvaluationService
from evidence_inspector.schemas import SupportLabel


def test_markdown_report_exposes_metrics_and_complete_claim_audit(
    tmp_path,
    sample_bundle,
) -> None:
    report = EvaluationService(tmp_path).evaluate(sample_bundle)
    markdown = (tmp_path / report.run_id / "report.md").read_text(encoding="utf-8")

    assert "- Classification counts:" in markdown
    for label in SupportLabel:
        assert (
            f"  - `{label.value}`: {report.metrics.classification_counts[label]}"
            in markdown
        )

    for assessment in report.assessments:
        assert f"### Claim `{assessment.claim_id}` — `{assessment.label.value}`" in markdown
        assert f"- Confidence: `{assessment.confidence:.3f}`" in markdown
        assert assessment.claim_text in markdown
        assert assessment.rationale in markdown
        for match in assessment.evidence_matches:
            assert (
                f"#### Evidence match `{match.evidence_id}` — score `{match.score:.3f}`"
                in markdown
            )
            assert match.excerpt in markdown
        for index, check in enumerate(assessment.quote_checks, start=1):
            outcome = "PASS" if check.exact_match else "FAIL"
            assert f"#### Exact-quote check {index} — `{outcome}`" in markdown
            assert check.quote in markdown

    assert "## Human review queue" in markdown
    assert "### Quality" in markdown
    assert "### Task fit" in markdown
    assert "### Efficiency" in markdown
    assert "not a model-price ranking" in markdown
    assert "combined into one effectiveness score" in markdown
    assert "Not scored as cost per token or model list price." in markdown
    assert "- Requirement coverage:" in markdown
    assert "- Requirement mapping macro-F1:" in markdown
    assert "the only join of quality, task fit, and efficiency" in markdown
    assert "predict supplied expected labels" in markdown
    assert f"- Review target: `{report.run_id}`" in markdown
    assert "`reviews.jsonl`" in markdown
    assert render_markdown(report) == markdown


def test_markdown_report_uses_non_colliding_fences_for_untrusted_text(
    tmp_path,
    sample_bundle,
) -> None:
    report = EvaluationService(tmp_path).evaluate(sample_bundle)
    attack = "Untrusted provider text.\n```\n## Forged audit section\n```"
    assessment = report.assessments[0].model_copy(update={"rationale": attack})
    changed = report.model_copy(
        update={"assessments": [assessment, *report.assessments[1:]]}
    )

    markdown = render_markdown(changed)

    assert f"Rationale:\n\n````text\n{attack}\n````" in markdown
    assert "\n```text\nUntrusted provider text." not in markdown


def test_markdown_report_states_unscored_quality_when_no_expected_claims(
    tmp_path,
    sample_bundle,
) -> None:
    unscored = sample_bundle.model_copy(update={"expected_claims": []})
    report = EvaluationService(tmp_path).evaluate(unscored)
    markdown = (tmp_path / report.run_id / "report.md").read_text(encoding="utf-8")

    assert report.metrics.classification_macro_f1 is None
    assert "complete expected claims were not supplied" in markdown
    assert "### Quality" in markdown
    assert "### Efficiency" in markdown
