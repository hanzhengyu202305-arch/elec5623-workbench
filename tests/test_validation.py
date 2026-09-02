from evidence_inspector.schemas import Claim, EvidenceItem
from evidence_inspector.validation import cited_evidence_ids, validate_exact_quotes


def test_citations_are_deduplicated_in_source_order() -> None:
    claim = Claim(id="c001", text="One [E1], two [evidence:E2], again [E1].")
    assert cited_evidence_ids(claim) == ["E1", "E2"]


def test_exact_quote_requires_cited_source() -> None:
    claim = Claim(id="c001", text='The report says "append-only" [E1].')
    evidence = [EvidenceItem(id="E1", title="Rule", content="Reviews are append-only.")]
    checks = validate_exact_quotes(claim, ["E1"], evidence)
    assert checks[0].exact_match is True
    altered = Claim(id="c002", text='The report says "append always" [E1].')
    assert validate_exact_quotes(altered, ["E1"], evidence)[0].exact_match is False

