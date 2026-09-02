"""Command-line interface for validate, evaluate, compare, and append-only review."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from .compare import ComparisonService, parse_model_names
from .engine import EvaluationService
from .errors import EvidenceInspectorError
from .gateway import build_gateway_from_environment
from .schemas import EvaluationBundle, HumanReviewInput


def _load_bundle(path: Path) -> EvaluationBundle:
    return EvaluationBundle.model_validate_json(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evidence-inspector")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate a bundle without creating a run")
    validate.add_argument("bundle", type=Path)

    evaluate = subparsers.add_parser("evaluate", help="evaluate a bundle and create immutable artifacts")
    evaluate.add_argument("bundle", type=Path)
    evaluate.add_argument("--out", type=Path, default=Path("runs"))

    review = subparsers.add_parser("review", help="append a human review to an existing run")
    review.add_argument("run_id")
    review.add_argument("review", type=Path)
    review.add_argument(
        "--runs",
        type=Path,
        default=Path(os.environ.get("EVIDENCE_INSPECTOR_RUNS", "runs")),
    )

    compare = subparsers.add_parser(
        "compare",
        help="evaluate the same bundle under at least two named models",
    )
    compare.add_argument("bundle", type=Path)
    compare.add_argument("--out", type=Path, required=True)
    compare.add_argument(
        "--models",
        required=True,
        help="comma-separated unique known model names (at least two)",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            bundle = _load_bundle(args.bundle)
            claims = EvaluationService().validate(bundle)
            print(
                json.dumps(
                    {
                        "valid": True,
                        "bundle_id": bundle.bundle_id,
                        "requirements": len(bundle.requirements),
                        "evidence": len(bundle.evidence),
                        "claims": len(claims),
                        "ground_truth_claims": len(bundle.expected_claims),
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "evaluate":
            report = EvaluationService(
                runs_dir=args.out,
                gateway=build_gateway_from_environment(),
            ).evaluate(_load_bundle(args.bundle))
            print(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True))
            return 0
        if args.command == "review":
            review = HumanReviewInput.model_validate_json(args.review.read_text(encoding="utf-8"))
            record = EvaluationService(runs_dir=args.runs).review(args.run_id, review)
            print(json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True))
            return 0
        if args.command == "compare":
            bundle = _load_bundle(args.bundle)
            report = ComparisonService(runs_dir=args.out).compare(
                bundle,
                parse_model_names(args.models),
            )
            print(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True))
            return 0
    except (OSError, ValueError, ValidationError, EvidenceInspectorError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":  # pragma: no cover
    main()
