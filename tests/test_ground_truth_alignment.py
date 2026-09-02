from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from evidence_inspector.api import create_app
from evidence_inspector.cli import run
from evidence_inspector.engine import EvaluationService
from evidence_inspector.errors import GroundTruthAlignmentError
from evidence_inspector.gateway import FixtureModelGateway
from evidence_inspector.schemas import EvaluationBundle


def _misaligned_bundle(sample_bundle, mode: str) -> EvaluationBundle:
    data = sample_bundle.model_dump(mode="json")
    if mode == "missing":
        data["expected_claims"] = data["expected_claims"][:-1]
    else:
        data["expected_claims"][-1]["claim_id"] = "c999"
    return EvaluationBundle.model_validate(data)


@pytest.mark.parametrize("mode", ["missing", "unknown"])
def test_ground_truth_drift_fails_before_provider_and_artifact_creation(
    tmp_path,
    sample_bundle,
    mode,
) -> None:
    bundle = _misaligned_bundle(sample_bundle, mode)

    with pytest.raises(GroundTruthAlignmentError, match="ground truth must cover"):
        EvaluationService(
            tmp_path,
            gateway=FixtureModelGateway(fail_mode="timeout"),
        ).evaluate(bundle)

    assert not tmp_path.exists() or list(tmp_path.iterdir()) == []


def test_cli_validate_runs_semantic_ground_truth_alignment(
    tmp_path,
    sample_bundle,
    capsys,
) -> None:
    bundle_path = tmp_path / "misaligned.json"
    bundle_path.write_text(
        _misaligned_bundle(sample_bundle, "missing").model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )

    assert run(["validate", str(bundle_path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "ground truth must cover every segmented claim exactly" in captured.err


def test_api_rejects_ground_truth_drift_without_a_completed_run(
    tmp_path,
    sample_bundle,
) -> None:
    client = TestClient(create_app(runs_dir=tmp_path))

    response = client.post(
        "/v1/evaluations",
        json=json.loads(_misaligned_bundle(sample_bundle, "unknown").model_dump_json()),
    )

    assert response.status_code == 400
    assert "ground truth must cover every segmented claim exactly" in response.json()["detail"]
    assert list(tmp_path.iterdir()) == []
