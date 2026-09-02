from evidence_inspector.segmentation import segment_claims


def test_markdown_segmentation_is_stable() -> None:
    markdown = "# Heading\n\n- First claim.\n- Second claim!\n\nThird claim? Fourth claim."
    first = segment_claims(markdown)
    second = segment_claims(markdown)
    assert [claim.id for claim in first] == ["c001", "c002", "c003", "c004"]
    assert first == second


def test_code_blocks_are_not_treated_as_claims() -> None:
    claims = segment_claims("Before.\n```python\nprint('not a claim')\n```\nAfter.")
    assert [claim.text for claim in claims] == ["Before.", "After."]


def test_heading_and_fenced_code_only_have_no_auditable_claims() -> None:
    markdown = "# Heading only\n\n```python\nprint('not auditable prose')\n```"
    assert segment_claims(markdown) == []


def test_commonmark_tilde_fence_and_setext_heading_are_ignored() -> None:
    markdown = (
        "Setext heading\n=======\n\n"
        "~~~python\nprint('not a claim')\n~~~~\n\n"
        "A real auditable claim."
    )
    claims = segment_claims(markdown)
    assert [claim.text for claim in claims] == ["A real auditable claim."]
