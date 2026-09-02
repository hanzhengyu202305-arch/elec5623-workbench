#!/usr/bin/env python3
"""Run fixture-only B0, ablation, and error analysis on the draft corpus."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evidence_inspector.engine import EngineConfig, EvaluationService
from evidence_inspector.gateway import FixtureModelGateway
from evidence_inspector.retrieval import EvidenceRetriever, map_requirements
from evidence_inspector.schemas import EvaluationBundle, RunReport, SupportLabel
from evidence_inspector.segmentation import segment_claims
from evidence_inspector.validation import cited_evidence_ids, validate_exact_quotes


STUDY_STATUS = "DRAFT_DEV_UNFROZEN_NOT_TUTOR_APPROVED"
VARIANT_DEFINITIONS = {
    "citation_presence_b0": (
        "Labels every claim with a known explicit citation as SUPPORTED; it has no "
        "lexical support, contradiction, quote, or requirement reasoning."
    ),
    "full_fixture_replay": (
        "Replays the implemented fixture pipeline with cited evidence first, exact-quote "
        "failure closure, and requirement mapping."
    ),
    "ablation_no_citation_priority": (
        "Uses only lexical top-k ordering at the gateway and does not place explicitly "
        "cited evidence first."
    ),
    "ablation_no_exact_quote_guard": (
        "Keeps the fixture classifier but omits the deterministic altered-quote override."
    ),
    "ablation_no_requirement_mapping": (
        "Keeps classification unchanged but removes all claim-to-requirement mappings."
    ),
}


def _load_script(name: str):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load study dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _prf(expected: set[str], actual: set[str]) -> tuple[float, float, float]:
    true_positive = len(expected & actual)
    precision = true_positive / len(actual) if actual else 0.0
    recall = true_positive / len(expected) if expected else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def _prediction_metrics(
    bundles: list[EvaluationBundle], rows: list[dict[str, Any]]
) -> dict[str, float]:
    expected_labels = {row["claim"]: row["expected_label"] for row in rows}
    actual_labels = {row["claim"]: row["actual_label"] for row in rows}
    label_f1 = []
    for label in SupportLabel:
        expected = {
            claim for claim, value in expected_labels.items() if value == label.value
        }
        actual = {claim for claim, value in actual_labels.items() if value == label.value}
        label_f1.append(_prf(expected, actual)[2])

    risky = {SupportLabel.UNSUPPORTED.value, SupportLabel.CONTRADICTED.value}
    expected_risky = {
        claim for claim, value in expected_labels.items() if value in risky
    }
    actual_risky = {claim for claim, value in actual_labels.items() if value in risky}
    risky_precision, risky_recall, _ = _prf(expected_risky, actual_risky)

    expected_by_claim = {
        row["claim"]: set(row["expected_requirements"]) for row in rows
    }
    actual_by_claim = {
        row["claim"]: set(row["actual_requirements"]) for row in rows
    }
    mapping_f1 = []
    for bundle in bundles:
        for requirement in bundle.requirements:
            prefix = f"{bundle.bundle_id}::"
            expected = {
                claim
                for claim, values in expected_by_claim.items()
                if claim.startswith(prefix) and requirement.id in values
            }
            actual = {
                claim
                for claim, values in actual_by_claim.items()
                if claim.startswith(prefix) and requirement.id in values
            }
            mapping_f1.append(_prf(expected, actual)[2])

    return {
        "citation_completeness": sum(row["citation_complete"] for row in rows)
        / len(rows),
        "classification_macro_f1": sum(label_f1) / len(label_f1),
        "risky_precision": risky_precision,
        "risky_recall": risky_recall,
        "requirement_mapping_macro_f1": sum(mapping_f1) / len(mapping_f1),
    }


def _confusion(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    matrix: dict[str, dict[str, int]] = {
        expected.value: {actual.value: 0 for actual in SupportLabel}
        for expected in SupportLabel
    }
    for row in rows:
        matrix[row["expected_label"]][row["actual_label"]] += 1
    return matrix


def _error_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "claim": row["claim"],
            "claim_text": row["claim_text"],
            "expected_label": row["expected_label"],
            "actual_label": row["actual_label"],
            "expected_requirements": row["expected_requirements"],
            "actual_requirements": row["actual_requirements"],
            "label_error": row["expected_label"] != row["actual_label"],
            "mapping_error": row["expected_requirements"]
            != row["actual_requirements"],
        }
        for row in rows
        if row["expected_label"] != row["actual_label"]
        or row["expected_requirements"] != row["actual_requirements"]
    ]


def _variant_rows(
    bundles: list[EvaluationBundle],
    *,
    citation_only: bool = False,
    prioritize_citations: bool = True,
    quote_guard: bool = True,
    requirement_mapping: bool = True,
) -> list[dict[str, Any]]:
    gateway = FixtureModelGateway()
    rows: list[dict[str, Any]] = []
    for bundle in bundles:
        expected_by_id = {item.claim_id: item for item in bundle.expected_claims}
        known_evidence = {item.id for item in bundle.evidence}
        retriever = EvidenceRetriever(bundle.evidence)
        for claim in segment_claims(bundle.generated_output.markdown):
            citations = cited_evidence_ids(claim)
            all_matches = retriever.retrieve(claim, top_k=len(bundle.evidence))
            matches_by_id = {match.evidence_id: match for match in all_matches}
            cited_matches = [
                matches_by_id[item] for item in citations if item in matches_by_id
            ]
            matches = all_matches[: EngineConfig().top_k]
            if prioritize_citations:
                for cited_match in cited_matches:
                    if cited_match.evidence_id not in {
                        item.evidence_id for item in matches
                    }:
                        matches.append(cited_match)
                gateway_matches = cited_matches + [
                    match
                    for match in matches
                    if match.evidence_id not in set(citations)
                ]
            else:
                gateway_matches = matches

            unknown_citations = set(citations) - known_evidence
            if citation_only:
                label = (
                    SupportLabel.UNSUPPORTED
                    if unknown_citations
                    else SupportLabel.SUPPORTED
                    if citations
                    else SupportLabel.INSUFFICIENT_EVIDENCE
                )
            else:
                label = gateway.classify(claim, gateway_matches).label
                quote_checks = validate_exact_quotes(
                    claim, citations, bundle.evidence
                )
                if unknown_citations:
                    label = SupportLabel.UNSUPPORTED
                elif quote_guard and any(
                    not check.exact_match for check in quote_checks
                ):
                    label = SupportLabel.UNSUPPORTED
                elif not citations and label in {
                    SupportLabel.SUPPORTED,
                    SupportLabel.PARTIALLY_SUPPORTED,
                }:
                    label = SupportLabel.UNSUPPORTED

            expected = expected_by_id[claim.id]
            actual_requirements = (
                sorted(map_requirements(claim, bundle.requirements))
                if requirement_mapping
                else []
            )
            rows.append(
                {
                    "claim": f"{bundle.bundle_id}::{claim.id}",
                    "claim_text": claim.text,
                    "expected_label": expected.label.value,
                    "actual_label": label.value,
                    "expected_requirements": sorted(expected.requirement_ids),
                    "actual_requirements": actual_requirements,
                    "citation_complete": bool(citations)
                    and all(item in known_evidence for item in citations),
                }
            )
    return rows


def _service_rows(
    bundles: list[EvaluationBundle], reports: list[RunReport]
) -> list[dict[str, Any]]:
    reports_by_bundle = {report.bundle_id: report for report in reports}
    rows: list[dict[str, Any]] = []
    for bundle in bundles:
        expected_by_id = {item.claim_id: item for item in bundle.expected_claims}
        known_evidence = {item.id for item in bundle.evidence}
        for assessment in reports_by_bundle[bundle.bundle_id].assessments:
            expected = expected_by_id[assessment.claim_id]
            rows.append(
                {
                    "claim": f"{bundle.bundle_id}::{assessment.claim_id}",
                    "claim_text": assessment.claim_text,
                    "expected_label": expected.label.value,
                    "actual_label": assessment.label.value,
                    "expected_requirements": sorted(expected.requirement_ids),
                    "actual_requirements": sorted(assessment.requirement_ids),
                    "citation_complete": bool(assessment.cited_evidence_ids)
                    and all(
                        item in known_evidence
                        for item in assessment.cited_evidence_ids
                    ),
                }
            )
    return rows


def _prediction_payload(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "claim": row["claim"],
            "expected_label": row["expected_label"],
            "actual_label": row["actual_label"],
            "expected_requirements": row["expected_requirements"],
            "actual_requirements": row["actual_requirements"],
        }
        for row in rows
    ]


def execute_study(
    bundles: list[EvaluationBundle], runs_dir: Path
) -> dict[str, Any]:
    acceptance = _load_script("run_corpus_acceptance.py")
    acceptance.validate_corpus_alignment(bundles)
    started = time.perf_counter()
    service = EvaluationService(runs_dir=runs_dir, gateway=FixtureModelGateway())
    reports = [service.evaluate(bundle) for bundle in bundles]
    elapsed_seconds = time.perf_counter() - started
    service_rows = _service_rows(bundles, reports)

    variants = {
        "citation_presence_b0": _variant_rows(
            bundles, citation_only=True, requirement_mapping=False
        ),
        "full_fixture_replay": _variant_rows(bundles),
        "ablation_no_citation_priority": _variant_rows(
            bundles, prioritize_citations=False
        ),
        "ablation_no_exact_quote_guard": _variant_rows(
            bundles, quote_guard=False
        ),
        "ablation_no_requirement_mapping": _variant_rows(
            bundles, requirement_mapping=False
        ),
    }
    service_prediction_sha256 = _canonical_sha256(
        _prediction_payload(service_rows)
    )
    full_replay_sha256 = _canonical_sha256(
        _prediction_payload(variants["full_fixture_replay"])
    )
    full_metrics = _prediction_metrics(
        bundles, variants["full_fixture_replay"]
    )
    variant_reports: dict[str, Any] = {}
    for name, rows in variants.items():
        metrics = _prediction_metrics(bundles, rows)
        errors = _error_rows(rows)
        variant_reports[name] = {
            "definition": VARIANT_DEFINITIONS[name],
            "metrics": metrics,
            "delta_vs_full": {
                key: metrics[key] - full_metrics[key] for key in sorted(metrics)
            },
            "confusion_matrix": _confusion(rows),
            "error_count": len(errors),
            "label_error_count": sum(error["label_error"] for error in errors),
            "mapping_error_count": sum(error["mapping_error"] for error in errors),
            "errors": errors,
            "prediction_sha256": _canonical_sha256(
                _prediction_payload(rows)
            ),
        }

    thresholds_pass = all(
        full_metrics[name] >= threshold
        for name, threshold in acceptance.THRESHOLDS.items()
    )
    replay_matches_service = full_replay_sha256 == service_prediction_sha256
    corpus_payload = [bundle.model_dump(mode="json") for bundle in bundles]
    return {
        "schema_version": "1.0",
        "status": "PASS" if thresholds_pass and replay_matches_service else "FAIL",
        "study_status": STUDY_STATUS,
        "tutor_approval_claimed": False,
        "external_api_used": False,
        "gateway": "fixture-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "counts": {
            "bundles": len(bundles),
            "claims": len(service_rows),
            "template_families": len(
                {bundle.generated_output.model.split(":")[1] for bundle in bundles}
            ),
            "markdown_layouts": len(
                {bundle.generated_output.model.split(":")[2] for bundle in bundles}
            ),
        },
        "elapsed_seconds": elapsed_seconds,
        "corpus_sha256": _canonical_sha256(corpus_payload),
        "service_prediction_sha256": service_prediction_sha256,
        "checks": {
            "full_replay_matches_service": replay_matches_service,
            "full_fixture_meets_draft_thresholds": thresholds_pass,
            "corpus_is_frozen": False,
            "tutor_approval_claimed": False,
            "external_api_used": False,
        },
        "thresholds": acceptance.THRESHOLDS,
        "variants": variant_reports,
        "limitations": [
            "The corpus is deterministic, synthetic, dev-only, and not frozen.",
            "Template-family diversity does not demonstrate out-of-distribution generalization.",
            "The fixture gateway is a transparent lexical baseline, not a live model evaluation.",
            "All labels and requirement mappings still require a documented human annotation review.",
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.runs_dir.exists():
            raise FileExistsError(
                f"refusing to reuse baseline-study runs directory: {args.runs_dir}"
            )
        if args.out.exists():
            raise FileExistsError(
                f"refusing to overwrite baseline-study report: {args.out}"
            )
        bundles = _load_script("generate_synthetic_corpus.py").build_corpus()
        report = execute_study(bundles, args.runs_dir)
        write_report(args.out, report)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
