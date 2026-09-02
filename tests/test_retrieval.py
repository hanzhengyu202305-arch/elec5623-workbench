from evidence_inspector.retrieval import EvidenceRetriever, map_requirements
from evidence_inspector.schemas import Claim, EvidenceItem, Requirement


def test_retrieval_returns_bounded_ranked_matches() -> None:
    evidence = [
        EvidenceItem(id="E1", title="Fruit", content="A red apple grows on a tree."),
        EvidenceItem(id="E2", title="Vehicle", content="A train follows a railway line."),
    ]
    result = EvidenceRetriever(evidence).retrieve(Claim(id="c001", text="The apple is red."), 2)
    assert result[0].evidence_id == "E1"
    assert all(0.0 <= item.score <= 1.0 for item in result)


def test_requirement_mapping_only_returns_known_ids() -> None:
    requirements = [
        Requirement(id="R1", text="Export an audit report as JSON."),
        Requirement(id="R2", text="Send a weather alert."),
    ]
    mapped = map_requirements(Claim(id="c001", text="The JSON audit report is exported."), requirements)
    assert mapped[0] == "R1"
    assert set(mapped) <= {"R1", "R2"}

