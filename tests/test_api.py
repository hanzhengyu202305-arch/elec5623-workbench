from fastapi.testclient import TestClient

from evidence_inspector.api import create_app


def test_four_api_contracts(tmp_path, sample_bundle) -> None:
    client = TestClient(create_app(runs_dir=tmp_path))
    health = client.get("/health")
    assert health.status_code == 200
    created = client.post("/v1/evaluations", json=sample_bundle.model_dump(mode="json"))
    assert created.status_code == 201
    run_id = created.json()["run_id"]
    fetched = client.get(f"/v1/evaluations/{run_id}")
    assert fetched.status_code == 200
    assert fetched.json()["input_sha256"] == created.json()["input_sha256"]
    reviewed = client.post(
        f"/v1/evaluations/{run_id}/reviews",
        json={
            "reviewer": "api-tester",
            "decision": "ACCEPT",
            "notes": "Trace checked against synthetic evidence.",
        },
    )
    assert reviewed.status_code == 201
    assert reviewed.json()["run_id"] == run_id


def test_api_returns_404_for_unknown_run(tmp_path) -> None:
    client = TestClient(create_app(runs_dir=tmp_path))
    response = client.get("/v1/evaluations/not-found")
    assert response.status_code == 404


def test_api_fails_closed_when_output_has_no_auditable_claims(tmp_path, sample_bundle) -> None:
    client = TestClient(create_app(runs_dir=tmp_path))
    data = sample_bundle.model_dump(mode="json")
    data["generated_output"]["markdown"] = "# Heading\n\n```text\ncode only\n```"
    data["expected_claims"] = []
    response = client.post("/v1/evaluations", json=data)
    assert response.status_code == 400
    assert "no auditable prose" in response.json()["detail"]
    assert list(tmp_path.iterdir()) == []


def test_api_review_rejects_aliased_target_without_touching_victim(
    tmp_path,
    sample_bundle,
) -> None:
    runs_dir = tmp_path / "runs"
    client = TestClient(create_app(runs_dir=runs_dir))
    created = client.post(
        "/v1/evaluations",
        json=sample_bundle.model_dump(mode="json"),
    )
    assert created.status_code == 201
    run_id = created.json()["run_id"]
    victim = tmp_path / "api-victim.log"
    victim.write_text("outside-authoritative-content\n", encoding="utf-8")
    reviews_path = runs_dir / run_id / "reviews.jsonl"
    reviews_path.symlink_to(victim)

    response = client.post(
        f"/v1/evaluations/{run_id}/reviews",
        json={
            "reviewer": "api-alias-test",
            "decision": "ACCEPT",
            "notes": "This must fail before an aliased append.",
        },
    )

    assert response.status_code == 400
    assert "review target" in response.json()["detail"]
    assert victim.read_text(encoding="utf-8") == "outside-authoritative-content\n"
