#!/usr/bin/env python3
"""Run and retain a fixture-only draft corpus acceptance report."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evidence_inspector.engine import EvaluationService
from evidence_inspector.gateway import FixtureModelGateway
from evidence_inspector.schemas import EvaluationBundle, RunReport, SupportLabel
from evidence_inspector.segmentation import segment_claims


CORPUS_STATUS = "DRAFT_UNFROZEN_NOT_TUTOR_APPROVED"
THRESHOLDS = {
    "citation_completeness": 1.0,
    "classification_macro_f1": 0.65,
    "risky_precision": 0.80,
    "risky_recall": 0.75,
    "requirement_mapping_macro_f1": 0.70,
}
MAX_ELAPSED_SECONDS = 60.0


def _generator_module():
    path = Path(__file__).with_name("generate_synthetic_corpus.py")
    spec = importlib.util.spec_from_file_location("evidence_inspector_corpus_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load corpus generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_bundles(corpus_dir: Path | None) -> tuple[list[EvaluationBundle], str]:
    if corpus_dir is None:
        return _generator_module().build_corpus(), "constructed-from-deterministic-generator"
    paths = sorted(corpus_dir.glob("synthetic-*.json"))
    bundles = [
        EvaluationBundle.model_validate_json(path.read_text(encoding="utf-8")) for path in paths
    ]
    return bundles, f"read-from:{corpus_dir.resolve()}"


def _prf(expected: set[str], actual: set[str]) -> tuple[float, float, float]:
    true_positive = len(expected & actual)
    precision = true_positive / len(actual) if actual else 0.0
    recall = true_positive / len(expected) if expected else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def aggregate_metrics(
    bundles: list[EvaluationBundle], reports: list[RunReport]
) -> tuple[dict[str, float], str]:
    reports_by_bundle = {report.bundle_id: report for report in reports}
    expected_labels: dict[str, SupportLabel] = {}
    actual_labels: dict[str, SupportLabel] = {}
    expected_mappings: dict[str, set[str]] = {}
    actual_mappings: dict[str, set[str]] = {}
    complete_citations = 0
    predictions: list[dict[str, Any]] = []

    for bundle in bundles:
        report = reports_by_bundle[bundle.bundle_id]
        expected_by_id = {item.claim_id: item for item in bundle.expected_claims}
        known_evidence = {item.id for item in bundle.evidence}
        for assessment in report.assessments:
            scoped_claim = f"{bundle.bundle_id}::{assessment.claim_id}"
            expected = expected_by_id[assessment.claim_id]
            expected_labels[scoped_claim] = expected.label
            actual_labels[scoped_claim] = assessment.label
            complete_citations += int(
                bool(assessment.cited_evidence_ids)
                and all(item in known_evidence for item in assessment.cited_evidence_ids)
            )
            predictions.append(
                {
                    "claim": scoped_claim,
                    "expected_label": expected.label.value,
                    "actual_label": assessment.label.value,
                    "expected_requirements": sorted(expected.requirement_ids),
                    "actual_requirements": sorted(assessment.requirement_ids),
                }
            )
        for requirement in bundle.requirements:
            scoped_requirement = f"{bundle.bundle_id}::{requirement.id}"
            expected_mappings[scoped_requirement] = {
                f"{bundle.bundle_id}::{item.claim_id}"
                for item in bundle.expected_claims
                if requirement.id in item.requirement_ids
            }
            actual_mappings[scoped_requirement] = {
                f"{bundle.bundle_id}::{item.claim_id}"
                for item in report.assessments
                if requirement.id in item.requirement_ids
            }

    claim_count = len(actual_labels)
    label_f1 = []
    for label in SupportLabel:
        expected = {claim for claim, value in expected_labels.items() if value == label}
        actual = {claim for claim, value in actual_labels.items() if value == label}
        label_f1.append(_prf(expected, actual)[2])
    risky = {SupportLabel.UNSUPPORTED, SupportLabel.CONTRADICTED}
    expected_risky = {claim for claim, value in expected_labels.items() if value in risky}
    actual_risky = {claim for claim, value in actual_labels.items() if value in risky}
    risky_precision, risky_recall, _ = _prf(expected_risky, actual_risky)
    mapping_f1 = [
        _prf(expected_mappings[item], actual_mappings[item])[2]
        for item in sorted(expected_mappings)
    ]
    metrics = {
        "citation_completeness": complete_citations / claim_count if claim_count else 0.0,
        "classification_macro_f1": sum(label_f1) / len(label_f1),
        "risky_precision": risky_precision,
        "risky_recall": risky_recall,
        "requirement_mapping_macro_f1": sum(mapping_f1) / len(mapping_f1) if mapping_f1 else 0.0,
    }
    return metrics, _canonical_sha256(predictions)


def build_checks(metrics: dict[str, float], elapsed_seconds: float) -> dict[str, dict[str, Any]]:
    checks: dict[str, dict[str, Any]] = {
        name: {
            "operator": ">=",
            "threshold": threshold,
            "actual": metrics[name],
            "passed": metrics[name] >= threshold,
        }
        for name, threshold in THRESHOLDS.items()
    }
    checks["elapsed_seconds"] = {
        "operator": "<=",
        "threshold": MAX_ELAPSED_SECONDS,
        "actual": elapsed_seconds,
        "passed": elapsed_seconds <= MAX_ELAPSED_SECONDS,
    }
    return checks


def validate_corpus_alignment(bundles: list[EvaluationBundle]) -> None:
    """Validate all cross-bundle invariants before the first run is created."""

    expected_claim_count = sum(len(bundle.expected_claims) for bundle in bundles)
    if len(bundles) != 20 or expected_claim_count != 200:
        raise ValueError(
            f"acceptance requires exactly 20 bundles and 200 expected claims; "
            f"received {len(bundles)} bundles and {expected_claim_count} claims"
        )
    id_counts = Counter(bundle.bundle_id for bundle in bundles)
    duplicates = sorted(bundle_id for bundle_id, count in id_counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"bundle ids must be globally unique; duplicates: {duplicates}")
    for bundle in bundles:
        expected_ids = [item.claim_id for item in bundle.expected_claims]
        actual_ids = [
            item.id for item in segment_claims(bundle.generated_output.markdown)
        ]
        if actual_ids != expected_ids:
            raise ValueError(
                f"expected claim ids do not align with segmentation for {bundle.bundle_id}: "
                f"expected {expected_ids}, actual {actual_ids}"
            )


def execute_acceptance(bundles: list[EvaluationBundle], runs_dir: Path) -> dict[str, Any]:
    validate_corpus_alignment(bundles)
    expected_claim_count = sum(len(bundle.expected_claims) for bundle in bundles)
    started = time.perf_counter()
    service = EvaluationService(runs_dir=runs_dir, gateway=FixtureModelGateway())
    reports = [service.evaluate(bundle) for bundle in bundles]
    elapsed_seconds = time.perf_counter() - started
    actual_claim_count = sum(report.metrics.claim_count for report in reports)
    if actual_claim_count != 200:
        raise ValueError(f"segmentation produced {actual_claim_count} claims; expected 200")
    metrics, prediction_sha256 = aggregate_metrics(bundles, reports)
    checks = build_checks(metrics, elapsed_seconds)
    corpus_payload = [bundle.model_dump(mode="json") for bundle in bundles]
    return {
        "schema_version": "1.0",
        "status": "PASS" if all(check["passed"] for check in checks.values()) else "FAIL",
        "corpus_status": CORPUS_STATUS,
        "tutor_approval_claimed": False,
        "gateway": "fixture-v1",
        "external_api_used": False,
        "generated_at": datetime.now(UTC).isoformat(),
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "counts": {
            "bundles": len(bundles),
            "expected_claims": expected_claim_count,
            "evaluated_claims": actual_claim_count,
        },
        "elapsed_seconds": elapsed_seconds,
        "metrics": metrics,
        "effectiveness": {
            "combined_index": False,
            "price_used_as_quality": False,
            "predicts": "supplied_expected_labels",
            "does_not_predict": [
                "token_spend",
                "model_list_price",
                "financial_outcome",
            ],
            "quality": {
                "citation_completeness": metrics["citation_completeness"],
                "classification_macro_f1": metrics["classification_macro_f1"],
                "risky_precision": metrics["risky_precision"],
                "risky_recall": metrics["risky_recall"],
            },
            "task_fit": {
                "requirement_mapping_macro_f1": metrics["requirement_mapping_macro_f1"],
            },
            "efficiency": {
                "elapsed_seconds": elapsed_seconds,
                "elapsed_seconds_limit": MAX_ELAPSED_SECONDS,
                "token_spend_aud": None,
            },
        },
        "checks": checks,
        "corpus_sha256": _canonical_sha256(corpus_payload),
        "prediction_sha256": prediction_sha256,
        "runs_dir": str(runs_dir.resolve()),
        "runs": [
            {
                "bundle_id": report.bundle_id,
                "run_id": report.run_id,
                "input_sha256": report.input_sha256,
                "status": report.status,
            }
            for report in reports
        ],
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        help="read synthetic-*.json from this directory; omit to construct deterministic draft bundles",
    )
    parser.add_argument("--runs-dir", type=Path, required=True, help="no-clobber run artifact root")
    parser.add_argument("--out", type=Path, required=True, help="new JSON acceptance report path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.out.exists():
            raise FileExistsError(f"refusing to overwrite acceptance report: {args.out}")
        bundles, source = load_bundles(args.corpus_dir)
        report = execute_acceptance(bundles, args.runs_dir)
        report["corpus_source"] = source
        write_report(args.out, report)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
