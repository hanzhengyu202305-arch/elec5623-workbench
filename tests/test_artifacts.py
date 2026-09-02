from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import threading

import pytest

import evidence_inspector.artifacts as artifacts_module
import evidence_inspector.engine as engine_module
from evidence_inspector.engine import EvaluationService
from evidence_inspector.errors import ArtifactIntegrityError, RunNotFound
from evidence_inspector.schemas import HumanReviewInput


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_repeated_evaluation_never_clobbers(tmp_path, sample_bundle) -> None:
    service = EvaluationService(tmp_path)
    first = service.evaluate(sample_bundle)
    second = service.evaluate(sample_bundle)
    assert first.run_id != second.run_id
    assert (tmp_path / first.run_id / "report.json").is_file()
    assert (tmp_path / second.run_id / "report.json").is_file()


def test_reviews_are_append_only_and_report_is_unchanged(tmp_path, sample_bundle) -> None:
    service = EvaluationService(tmp_path)
    report = service.evaluate(sample_bundle)
    report_path = tmp_path / report.run_id / "report.json"
    before = _sha256(report_path)
    review = HumanReviewInput(
        reviewer="tester",
        decision="NEEDS_CHANGES",
        notes="Needs supporting evidence.",
        claim_id="c009",
    )
    first = service.review(report.run_id, review)
    second = service.review(report.run_id, review)
    records = [
        json.loads(line)
        for line in (tmp_path / report.run_id / "reviews.jsonl").read_text().splitlines()
    ]
    assert len(records) == 2
    assert first.review_id != second.review_id
    assert _sha256(report_path) == before


def test_review_rejects_symlink_target_without_touching_victim(
    tmp_path,
    sample_bundle,
) -> None:
    service = EvaluationService(tmp_path / "runs")
    report = service.evaluate(sample_bundle)
    victim = tmp_path / "outside-review.log"
    victim.write_text("outside-authoritative-content\n", encoding="utf-8")
    reviews_path = service.store.root / report.run_id / "reviews.jsonl"
    reviews_path.symlink_to(victim)

    with pytest.raises(ArtifactIntegrityError, match="review target"):
        service.review(
            report.run_id,
            HumanReviewInput(
                reviewer="alias-test",
                decision="ACCEPT",
                notes="This must not be appended through a symlink.",
            ),
        )

    assert victim.read_text(encoding="utf-8") == "outside-authoritative-content\n"
    assert reviews_path.is_symlink()


def test_review_rejects_hardlink_target_without_touching_victim(
    tmp_path,
    sample_bundle,
) -> None:
    service = EvaluationService(tmp_path / "runs")
    report = service.evaluate(sample_bundle)
    victim = tmp_path / "outside-hardlink.log"
    victim.write_text("outside-authoritative-content\n", encoding="utf-8")
    reviews_path = service.store.root / report.run_id / "reviews.jsonl"
    os.link(victim, reviews_path)

    with pytest.raises(ArtifactIntegrityError, match="review target"):
        service.review(
            report.run_id,
            HumanReviewInput(
                reviewer="hardlink-test",
                decision="NEEDS_CHANGES",
                notes="This must not be appended through a hard link.",
            ),
        )

    assert victim.read_text(encoding="utf-8") == "outside-authoritative-content\n"


def test_read_and_review_reject_symlink_run_directory(
    tmp_path,
    sample_bundle,
) -> None:
    outside_service = EvaluationService(tmp_path / "outside-runs")
    outside_report = outside_service.evaluate(sample_bundle)
    service = EvaluationService(tmp_path / "runs")
    service.store.root.mkdir()
    alias = service.store.root / "aliased-run"
    alias.symlink_to(
        outside_service.store.root / outside_report.run_id,
        target_is_directory=True,
    )

    with pytest.raises(ArtifactIntegrityError, match="run directory"):
        service.get_report("aliased-run")
    with pytest.raises(ArtifactIntegrityError, match="run directory"):
        service.review(
            "aliased-run",
            HumanReviewInput(
                reviewer="run-alias-test",
                decision="REJECT",
                notes="This review target is outside the configured run root.",
            ),
        )

    assert not (
        outside_service.store.root / outside_report.run_id / "reviews.jsonl"
    ).exists()


def test_read_rejects_symlink_report_artifact(tmp_path, sample_bundle) -> None:
    outside_service = EvaluationService(tmp_path / "outside-runs")
    outside_report = outside_service.evaluate(sample_bundle)
    service = EvaluationService(tmp_path / "runs")
    aliased_run = service.store.root / "aliased-report"
    aliased_run.mkdir(parents=True)
    (aliased_run / "report.json").symlink_to(
        outside_service.store.root / outside_report.run_id / "report.json"
    )

    with pytest.raises(ArtifactIntegrityError, match="report artifact"):
        service.get_report("aliased-report")


def test_read_rejects_report_identity_mismatch(tmp_path, sample_bundle) -> None:
    service = EvaluationService(tmp_path)
    report = service.evaluate(sample_bundle)
    report_path = tmp_path / report.run_id / "report.json"
    changed = json.loads(report_path.read_text(encoding="utf-8"))
    changed["run_id"] = "different-valid-run"
    report_path.write_text(json.dumps(changed), encoding="utf-8")

    with pytest.raises(ArtifactIntegrityError, match="identity mismatch"):
        service.get_report(report.run_id)


def test_review_append_retries_short_writes(tmp_path, sample_bundle, monkeypatch) -> None:
    service = EvaluationService(tmp_path)
    report = service.evaluate(sample_bundle)
    real_write = artifacts_module.os.write
    write_sizes: list[int] = []

    def short_write(descriptor, content):
        chunk = memoryview(content)[: max(1, len(content) // 3)]
        written = real_write(descriptor, chunk)
        write_sizes.append(written)
        return written

    monkeypatch.setattr(artifacts_module.os, "write", short_write)
    record = service.review(
        report.run_id,
        HumanReviewInput(
            reviewer="short-write-reviewer",
            decision="ACCEPT",
            notes="Synthetic short-write durability test.",
            claim_id="c009",
        ),
    )

    records = [
        json.loads(line)
        for line in (tmp_path / report.run_id / "reviews.jsonl").read_text().splitlines()
    ]
    assert len(write_sizes) > 1
    assert records == [record.model_dump(mode="json")]


def test_review_append_rolls_back_when_write_makes_no_progress(
    tmp_path,
    sample_bundle,
    monkeypatch,
) -> None:
    service = EvaluationService(tmp_path)
    report = service.evaluate(sample_bundle)
    reviews_path = tmp_path / report.run_id / "reviews.jsonl"
    real_write = artifacts_module.os.write
    write_count = 0

    def partial_then_stalled(descriptor, content):
        nonlocal write_count
        write_count += 1
        if write_count == 1:
            return real_write(descriptor, memoryview(content)[:1])
        return 0

    monkeypatch.setattr(artifacts_module.os, "write", partial_then_stalled)
    with pytest.raises(OSError, match="made no progress"):
        service.review(
            report.run_id,
            HumanReviewInput(
                reviewer="stalled-reviewer",
                decision="NEEDS_CHANGES",
                notes="Synthetic zero-progress durability test.",
                claim_id="c009",
            ),
        )

    assert write_count == 2
    assert reviews_path.read_bytes() == b""


def test_concurrent_review_writers_produce_complete_unique_jsonl_records(
    tmp_path,
    sample_bundle,
) -> None:
    service = EvaluationService(tmp_path)
    report = service.evaluate(sample_bundle)
    writer_count = 12
    start = threading.Barrier(writer_count)

    def append_review(index: int):
        start.wait()
        return service.review(
            report.run_id,
            HumanReviewInput(
                reviewer=f"concurrent-reviewer-{index}",
                decision="NEEDS_CHANGES",
                notes=f"Synthetic concurrent append {index}.",
                claim_id="c009",
            ),
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=writer_count) as executor:
        returned = list(executor.map(append_review, range(writer_count)))

    records = [
        json.loads(line)
        for line in (tmp_path / report.run_id / "reviews.jsonl").read_text().splitlines()
    ]
    assert len(records) == writer_count
    assert len({record["review_id"] for record in records}) == writer_count
    assert {record["reviewer"] for record in records} == {
        f"concurrent-reviewer-{index}" for index in range(writer_count)
    }
    assert {record.review_id for record in returned} == {
        record["review_id"] for record in records
    }


def test_review_append_fails_closed_without_fcntl_locking(
    tmp_path,
    sample_bundle,
    monkeypatch,
) -> None:
    service = EvaluationService(tmp_path)
    report = service.evaluate(sample_bundle)
    reviews_path = tmp_path / report.run_id / "reviews.jsonl"
    monkeypatch.setattr(artifacts_module, "_fcntl", None)

    with pytest.raises(RuntimeError, match="locking is unavailable"):
        service.review(
            report.run_id,
            HumanReviewInput(
                reviewer="unsupported-platform-reviewer",
                decision="ACCEPT",
                notes="The unsafe fallback must never be used.",
                claim_id="c009",
            ),
        )

    assert not reviews_path.exists()


@pytest.mark.parametrize("failure_target", ["render", "report.md", "report.json"])
def test_failed_artifact_publish_has_no_readable_commit_marker(
    tmp_path, sample_bundle, monkeypatch, failure_target
) -> None:
    monkeypatch.setattr(
        engine_module,
        "_candidate_run_id",
        lambda bundle, digest, now: "fixed-failed-run",
    )
    if failure_target == "render":
        def fail_render(report):
            raise RuntimeError("synthetic render failure")

        monkeypatch.setattr(artifacts_module, "render_markdown", fail_render)
    else:
        real_write = artifacts_module._write_new

        def fail_write(path, content):
            if path.name == failure_target:
                raise OSError(f"synthetic write failure: {failure_target}")
            real_write(path, content)

        monkeypatch.setattr(artifacts_module, "_write_new", fail_write)

    service = EvaluationService(tmp_path)
    with pytest.raises((OSError, RuntimeError)):
        service.evaluate(sample_bundle)
    assert not (tmp_path / "fixed-failed-run").exists()
    with pytest.raises(RunNotFound):
        service.get_report("fixed-failed-run")
    assert list(tmp_path.iterdir()) == []


def test_atomic_file_publish_hides_partial_staging_bytes_on_interruption(
    tmp_path,
    monkeypatch,
) -> None:
    target = tmp_path / "report.json"

    def interrupt_after_partial_write(descriptor, content):
        artifacts_module.os.write(descriptor, memoryview(content)[:3])
        raise KeyboardInterrupt("synthetic interruption")

    monkeypatch.setattr(
        artifacts_module,
        "_write_all_and_fsync",
        interrupt_after_partial_write,
    )

    with pytest.raises(KeyboardInterrupt, match="synthetic interruption"):
        artifacts_module._write_new(target, '{"complete": true}\n')
    assert not target.exists()
    assert list(tmp_path.iterdir()) == []


def test_interrupted_report_marker_publish_leaves_no_readable_completed_run(
    tmp_path,
    sample_bundle,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        engine_module,
        "_candidate_run_id",
        lambda bundle, digest, now: "fixed-interrupted-run",
    )
    real_publish = artifacts_module._publish_no_clobber

    def interrupt_report_publish(staging_path, final_path):
        if final_path.name == "report.json":
            raise KeyboardInterrupt("synthetic report-marker interruption")
        real_publish(staging_path, final_path)

    monkeypatch.setattr(
        artifacts_module,
        "_publish_no_clobber",
        interrupt_report_publish,
    )
    service = EvaluationService(tmp_path)

    with pytest.raises(KeyboardInterrupt, match="report-marker interruption"):
        service.evaluate(sample_bundle)

    run_dir = tmp_path / "fixed-interrupted-run"
    assert sorted(path.name for path in run_dir.iterdir()) == [
        "input.bundle.json",
        "report.md",
    ]
    assert not any(path.name.endswith(".tmp") for path in run_dir.iterdir())
    with pytest.raises(RunNotFound):
        service.get_report("fixed-interrupted-run")


def test_report_json_is_the_last_atomically_published_artifact(
    tmp_path,
    sample_bundle,
    monkeypatch,
) -> None:
    published: list[str] = []
    real_publish = artifacts_module._publish_no_clobber

    def record_publish(staging_path, final_path):
        real_publish(staging_path, final_path)
        published.append(final_path.name)

    monkeypatch.setattr(artifacts_module, "_publish_no_clobber", record_publish)
    report = EvaluationService(tmp_path).evaluate(sample_bundle)

    assert published == ["input.bundle.json", "report.md", "report.json"]
    assert EvaluationService(tmp_path).get_report(report.run_id) == report
