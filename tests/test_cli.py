from __future__ import annotations

import json

from evidence_inspector.cli import run
from evidence_inspector.schemas import EvaluationBundle


def test_validate_and_evaluate_commands(tmp_path, capsys) -> None:
    from pathlib import Path

    project = Path(__file__).resolve().parents[1]
    bundle = project / "examples" / "sample_bundle.json"
    assert run(["validate", str(bundle)]) == 0
    validated = json.loads(capsys.readouterr().out)
    assert validated["valid"] is True
    assert validated["claims"] == 11
    assert validated["ground_truth_claims"] == 11
    assert run(["evaluate", str(bundle), "--out", str(tmp_path)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert (tmp_path / report["run_id"] / "report.json").is_file()


def test_review_command(tmp_path, capsys) -> None:
    from pathlib import Path

    project = Path(__file__).resolve().parents[1]
    bundle = project / "examples" / "sample_bundle.json"
    review = project / "examples" / "review.json"
    assert run(["evaluate", str(bundle), "--out", str(tmp_path)]) == 0
    run_id = json.loads(capsys.readouterr().out)["run_id"]
    assert run(["review", run_id, str(review), "--runs", str(tmp_path)]) == 0
    record = json.loads(capsys.readouterr().out)
    assert record["run_id"] == run_id


def test_cli_fails_closed_when_output_has_no_auditable_claims(
    tmp_path, capsys, sample_bundle
) -> None:
    data = sample_bundle.model_dump(mode="json")
    data["generated_output"]["markdown"] = "# Heading\n\n```text\ncode only\n```"
    data["expected_claims"] = []
    bundle_path = tmp_path / "no-claims.json"
    bundle_path.write_text(
        EvaluationBundle.model_validate(data).model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    runs_dir = tmp_path / "runs"
    assert run(["evaluate", str(bundle_path), "--out", str(runs_dir)]) == 2
    assert "no auditable prose" in capsys.readouterr().err
    assert not runs_dir.exists()


def test_cli_compare_happy_path(tmp_path, capsys) -> None:
    from pathlib import Path

    project = Path(__file__).resolve().parents[1]
    bundle = project / "examples" / "sample_bundle.json"
    out = tmp_path / "compare-out"
    assert (
        run(
            [
                "compare",
                str(bundle),
                "--out",
                str(out),
                "--models",
                "fixture,fixture-b",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "READY_FOR_HUMAN_REVIEW"
    assert (out / "compare.json").is_file()
    assert (out / "compare.md").is_file()
    assert len(payload["models"]) == 2
    for row in payload["models"]:
        assert (out / row["run_id"] / "report.json").is_file()


def test_cli_compare_requires_two_known_models(tmp_path, capsys) -> None:
    from pathlib import Path

    project = Path(__file__).resolve().parents[1]
    bundle = project / "examples" / "sample_bundle.json"
    out = tmp_path / "compare-out"
    assert run(["compare", str(bundle), "--out", str(out), "--models", "fixture"]) == 2
    err = capsys.readouterr().err
    assert err.startswith("error:")
    assert "at least two" in err
    assert not (out / "compare.json").exists()
    assert not (out / "compare.md").exists()

    assert (
        run(["compare", str(bundle), "--out", str(out), "--models", "fixture,unknown"])
        == 2
    )
    err = capsys.readouterr().err
    assert err.startswith("error:")
    assert "unknown model" in err
    assert not (out / "compare.json").exists()


def test_cli_review_rejects_aliased_target_without_touching_victim(
    tmp_path,
    capsys,
) -> None:
    from pathlib import Path

    project = Path(__file__).resolve().parents[1]
    bundle = project / "examples" / "sample_bundle.json"
    review = project / "examples" / "review.json"
    runs_dir = tmp_path / "runs"
    assert run(["evaluate", str(bundle), "--out", str(runs_dir)]) == 0
    run_id = json.loads(capsys.readouterr().out)["run_id"]
    victim = tmp_path / "cli-victim.log"
    victim.write_text("outside-authoritative-content\n", encoding="utf-8")
    reviews_path = runs_dir / run_id / "reviews.jsonl"
    reviews_path.symlink_to(victim)

    assert run(["review", run_id, str(review), "--runs", str(runs_dir)]) == 2

    assert "review target" in capsys.readouterr().err
    assert victim.read_text(encoding="utf-8") == "outside-authoritative-content\n"
