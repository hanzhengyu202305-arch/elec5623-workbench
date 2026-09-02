"""Immutable evaluation artifacts and append-only human reviews."""

from __future__ import annotations

import json
import os
import re
import stat
import uuid
from datetime import UTC, datetime
from pathlib import Path

try:
    import fcntl as _fcntl
except ImportError:  # pragma: no cover - exercised by the explicit fail-closed test
    _fcntl = None

from .errors import ArtifactIntegrityError, InvalidRunId, RunNotFound
from .schemas import (
    EvaluationBundle,
    EvaluationMetrics,
    HumanReviewInput,
    HumanReviewRecord,
    RunReport,
    SupportLabel,
)


_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def _file_identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _require_unaliased_regular_file(value: os.stat_result, label: str) -> None:
    if not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
        raise ArtifactIntegrityError(f"{label} must be one unaliased regular file")


def _read_unaliased_text(path: Path, label: str) -> str:
    """Read one stable regular file without following a final symlink."""

    snapshot = path.lstat()
    _require_unaliased_regular_file(snapshot, label)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    try:
        try:
            descriptor = os.open(path, flags)
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise ArtifactIntegrityError(
                f"{label} could not be opened without following an alias"
            ) from exc
        opened = os.fstat(descriptor)
        _require_unaliased_regular_file(opened, label)
        try:
            current = path.lstat()
        except OSError as exc:
            raise ArtifactIntegrityError(f"{label} changed while it was opened") from exc
        _require_unaliased_regular_file(current, label)
        if _file_identity(opened) != _file_identity(snapshot) or _file_identity(
            opened
        ) != _file_identity(current):
            raise ArtifactIntegrityError(f"{label} changed while it was opened")
        with os.fdopen(descriptor, encoding="utf-8") as stream:
            descriptor = -1
            return stream.read()
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _json_text(value: object) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _write_new(path: Path, content: str) -> None:
    """Publish a fully durable file without ever exposing partial final bytes."""

    staging_path = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    descriptor = -1
    try:
        descriptor = os.open(
            staging_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
        _write_all_and_fsync(descriptor, content.encode("utf-8"))
        os.close(descriptor)
        descriptor = -1

        # A hard link is an atomic no-clobber publication on the same filesystem.
        # The final name therefore appears only after every byte is durable.
        _publish_no_clobber(staging_path, path)
        staging_path.unlink()
        _fsync_directory(path.parent)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if staging_path.exists() or staging_path.is_symlink():
            staging_path.unlink()


def _write_all_and_fsync(descriptor: int, content: bytes) -> None:
    remaining = memoryview(content)
    while remaining:
        written = os.write(descriptor, remaining)
        if written <= 0:
            raise OSError("atomic artifact staging write made no progress")
        remaining = remaining[written:]
    os.fsync(descriptor)


def _publish_no_clobber(staging_path: Path, final_path: Path) -> None:
    os.link(staging_path, final_path)


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _append_record_durably(path: Path, content: bytes) -> None:
    """Append one complete record under an exclusive advisory file lock.

    POSIX does not guarantee that one ``os.write`` consumes the entire buffer.
    The lock therefore covers the original-size snapshot, every short-write
    retry, the final file ``fsync``, and rollback of an interrupted write.
    Platforms without ``fcntl.flock`` fail closed instead of silently using an
    unsafe append path.
    """

    if _fcntl is None:
        raise RuntimeError("append-only review locking is unavailable on this platform")

    snapshot: os.stat_result | None
    try:
        snapshot = path.lstat()
    except FileNotFoundError:
        snapshot = None
    if snapshot is not None:
        _require_unaliased_regular_file(snapshot, "review target")

    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise ArtifactIntegrityError(
            "review target could not be opened without following an alias"
        ) from exc
    try:
        opened = os.fstat(descriptor)
        _require_unaliased_regular_file(opened, "review target")
        try:
            current = path.lstat()
        except OSError as exc:
            raise ArtifactIntegrityError(
                "review target changed while it was opened"
            ) from exc
        _require_unaliased_regular_file(current, "review target")
        if snapshot is not None and _file_identity(opened) != _file_identity(snapshot):
            raise ArtifactIntegrityError("review target changed while it was opened")
        if _file_identity(opened) != _file_identity(current):
            raise ArtifactIntegrityError("review target changed while it was opened")
        _fcntl.flock(descriptor, _fcntl.LOCK_EX)
        _require_unaliased_regular_file(os.fstat(descriptor), "review target")
        original_size = os.fstat(descriptor).st_size
        try:
            _write_all_and_fsync(descriptor, content)
        except BaseException:
            try:
                os.ftruncate(descriptor, original_size)
                os.fsync(descriptor)
            except OSError as rollback_error:
                raise OSError(
                    "review append failed and partial-record rollback failed"
                ) from rollback_error
            raise
    finally:
        # Closing the descriptor releases flock even when writing or rollback fails.
        os.close(descriptor)


def _literal_block(value: str) -> list[str]:
    """Render untrusted text without allowing it to close its own code fence."""

    longest_run = max((len(match.group(0)) for match in re.finditer(r"`+", value)), default=0)
    fence = "`" * max(3, longest_run + 1)
    return [f"{fence}text", value, fence]


def render_markdown(report: RunReport) -> str:
    metrics = report.metrics
    lines = [
        f"# Evaluation run `{report.run_id}`",
        "",
        f"- Bundle: `{report.bundle_id}`",
        f"- Status: `{report.status}`",
        f"- Gateway: `{report.gateway}`",
        f"- Retrieval: `{report.retrieval_backend}`",
        f"- Created: `{report.created_at.isoformat()}`",
        f"- Input SHA-256: `{report.input_sha256}`",
        "",
        "## Metrics",
        "",
        "Quality, task fit, and efficiency are reported separately. They are not",
        "combined into one effectiveness score and are not a model-price ranking.",
        _annotation_prediction_line(metrics),
        "",
        "### Quality",
        "",
        f"- Claims: {metrics.claim_count}",
        f"- Citation completeness: {metrics.citation_completeness:.3f}",
        f"- Exact quote accuracy: {_format_optional(metrics.exact_quote_accuracy)}",
        f"- Classification macro-F1: {_format_optional(metrics.classification_macro_f1)}",
        f"- Risky precision: {_format_optional(metrics.risky_precision)}",
        f"- Risky recall: {_format_optional(metrics.risky_recall)}",
        "- Classification counts:",
        *(
            f"  - `{label.value}`: {metrics.classification_counts.get(label, 0)}"
            for label in SupportLabel
        ),
        "",
        "### Task fit",
        "",
        f"- Requirement coverage: {metrics.requirement_coverage:.3f}",
        f"- Requirement mapping macro-F1: {_format_optional(metrics.requirement_mapping_macro_f1)}",
        "",
        "### Efficiency",
        "",
        "- Not scored as cost per token or model list price.",
        "- Over-budget and unsafe input fail closed before a completed report exists.",
        "- Corpus elapsed time is checked separately against the 60.0 s / 200-claim bound.",
        "",
        "## Claim audit summary",
        "",
        "| Claim ID | Label | Confidence | Citations | Requirements |",
        "|---|---|---:|---|---|",
    ]
    for item in report.assessments:
        lines.append(
            f"| `{item.claim_id}` | `{item.label.value}` | {item.confidence:.3f} "
            f"| {', '.join(item.cited_evidence_ids) or '—'} "
            f"| {', '.join(item.requirement_ids) or '—'} |"
        )
    lines.extend(["", "## Detailed claim-evidence audit"])
    for item in report.assessments:
        lines.extend(
            [
                "",
                f"### Claim `{item.claim_id}` — `{item.label.value}`",
                "",
                f"- Confidence: `{item.confidence:.3f}`",
                f"- Cited evidence: {', '.join(f'`{value}`' for value in item.cited_evidence_ids) or '—'}",
                f"- Mapped requirements: {', '.join(f'`{value}`' for value in item.requirement_ids) or '—'}",
                "",
                "Claim text:",
                "",
                *_literal_block(item.claim_text),
                "",
                "Rationale:",
                "",
                *_literal_block(item.rationale),
                "",
                "#### Retrieved evidence",
            ]
        )
        if not item.evidence_matches:
            lines.extend(["", "No evidence matches were retrieved."])
        for match in item.evidence_matches:
            lines.extend(
                [
                    "",
                    f"#### Evidence match `{match.evidence_id}` — score `{match.score:.3f}`",
                    "",
                    "Excerpt:",
                    "",
                    *_literal_block(match.excerpt),
                ]
            )
        lines.extend(["", "#### Exact-quote validation"])
        if not item.quote_checks:
            lines.extend(["", "No quoted spans were present."])
        for index, check in enumerate(item.quote_checks, start=1):
            outcome = "PASS" if check.exact_match else "FAIL"
            evidence_id = f"`{check.evidence_id}`" if check.evidence_id else "—"
            lines.extend(
                [
                    "",
                    f"#### Exact-quote check {index} — `{outcome}`",
                    "",
                    f"- Matched evidence: {evidence_id}",
                    "",
                    "Quoted span:",
                    "",
                    *_literal_block(check.quote),
                ]
            )
    lines.extend(
        [
            "",
            "## Human review queue",
            "",
            f"- Review target: `{report.run_id}`",
            f"- Queue state: `{report.status}`",
            "- Append decisions through the CLI or review API; records are stored in "
            "`reviews.jsonl` without changing this evaluation report.",
            "- Automated output is decision support only and never constitutes approval.",
            "- The review queue is the only join of quality, task fit, and efficiency.",
            "",
        ]
    )
    return "\n".join(lines)


def _annotation_prediction_line(metrics: EvaluationMetrics) -> str:
    if metrics.classification_macro_f1 is None:
        return (
            "Quality and task-fit F1 are not scored on this run because complete "
            "expected claims were not supplied; they are not claims about spend."
        )
    return (
        "When scored, quality and task-fit predict supplied expected labels on "
        "this bundle. They do not predict token spend, list price, or savings."
    )


def _format_optional(value: float | None) -> str:
    return "not scored" if value is None else f"{value:.3f}"


class ArtifactStore:
    """Store no-clobber runs under one explicit root."""

    def __init__(self, root: Path | str):
        self.root = Path(root)

    def write_run(self, bundle: EvaluationBundle, report: RunReport) -> RunReport:
        self.root.mkdir(parents=True, exist_ok=True)
        base = report.run_id
        run_dir: Path | None = None
        actual_id = base
        for suffix in range(1000):
            actual_id = base if suffix == 0 else f"{base[:60]}-{suffix:02d}"
            candidate = self.root / actual_id
            try:
                candidate.mkdir()
            except FileExistsError:
                continue
            run_dir = candidate
            break
        if run_dir is None:
            raise FileExistsError(f"unable to reserve a unique run directory for {base}")
        stored_report = report.model_copy(update={"run_id": actual_id})
        try:
            # Render every artifact completely before the first file write.
            # A valid report.json is the final commit marker for a completed run.
            input_text = _json_text(bundle)
            markdown_text = render_markdown(stored_report)
            report_text = _json_text(stored_report)
            _write_new(run_dir / "input.bundle.json", input_text)
            _write_new(run_dir / "report.md", markdown_text)
            _write_new(run_dir / "report.json", report_text)
        except Exception:
            self._cleanup_failed_run(run_dir)
            raise
        return stored_report

    def read_report(self, run_id: str) -> RunReport:
        run_dir = self._run_dir(run_id)
        report_path = run_dir / "report.json"
        try:
            report_text = _read_unaliased_text(report_path, "report artifact")
        except FileNotFoundError:
            raise RunNotFound(f"run not found: {run_id}")
        try:
            report = RunReport.model_validate_json(report_text)
        except (UnicodeError, ValueError) as exc:
            raise ArtifactIntegrityError(
                f"report artifact is invalid for run {run_id}"
            ) from exc
        if report.run_id != run_id:
            raise ArtifactIntegrityError(
                f"report identity mismatch for run {run_id}: {report.run_id}"
            )
        return report

    def append_review(self, run_id: str, review: HumanReviewInput) -> HumanReviewRecord:
        report = self.read_report(run_id)
        if review.claim_id and review.claim_id not in {
            assessment.claim_id for assessment in report.assessments
        }:
            raise ValueError(f"claim does not exist in run {run_id}: {review.claim_id}")
        record = HumanReviewRecord(
            **review.model_dump(),
            review_id=f"r-{uuid.uuid4().hex[:16]}",
            run_id=run_id,
            reviewed_at=datetime.now(UTC),
        )
        payload = json.dumps(record.model_dump(mode="json"), sort_keys=True, ensure_ascii=False) + "\n"
        reviews_path = self._run_dir(run_id) / "reviews.jsonl"
        _append_record_durably(reviews_path, payload.encode("utf-8"))
        return record

    def _run_dir(self, run_id: str) -> Path:
        if not _RUN_ID.fullmatch(run_id):
            raise InvalidRunId("invalid run id")
        run_dir = self.root / run_id
        try:
            run_snapshot = run_dir.lstat()
        except FileNotFoundError:
            return run_dir
        if not stat.S_ISDIR(run_snapshot.st_mode):
            raise ArtifactIntegrityError(
                f"run directory must be a real directory under the artifact root: {run_id}"
            )
        return run_dir

    @staticmethod
    def _cleanup_failed_run(run_dir: Path) -> None:
        """Remove only the three explicitly known staging artifacts."""

        input_path = run_dir / "input.bundle.json"
        markdown_path = run_dir / "report.md"
        report_path = run_dir / "report.json"
        if report_path.exists():
            report_path.unlink()
        if markdown_path.exists():
            markdown_path.unlink()
        if input_path.exists():
            input_path.unlink()
        run_dir.rmdir()
