"""Multi-model comparison shell around the Inspector evaluation engine.

Public list prices are USD per million *input* tokens. Estimated cost is that
price multiplied by ``conservative_token_upper_bound`` (canonical UTF-8 byte
count). This is a conservative upper-bound estimate, not an invoice.

Published table (CLI-known names this week; live commercial APIs are out of
scope):

- ``fixture`` / ``fixture-v1``: 0.00 (deterministic CI baseline)
- ``fixture-b``: 0.50 (published mock list price so min-cost and quality can
  diverge)

Unknown gateway names fail closed instead of inventing a price.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from pathlib import Path

from .engine import EngineConfig, EvaluationService, conservative_token_upper_bound
from .errors import CompareIncompleteError, EvidenceInspectorError
from .gateway import FixtureModelGateway, ModelGateway
from .schemas import (
    ComparisonReport,
    ComparedModelResult,
    EvaluationBundle,
    RunReport,
    SelectionResult,
    SupportLabel,
)
from .segmentation import segment_claims


KNOWN_COMPARE_MODELS = ("fixture", "fixture-b")

# USD per million input tokens. Unknown names must not be given a silent price.
LIST_PRICE_USD_PER_MILLION_INPUT_TOKENS: dict[str, float] = {
    "fixture": 0.0,
    "fixture-v1": 0.0,
    "fixture-b": 0.50,
}

MIN_COST_RULE = (
    "Min-cost selects the lower estimated_cost_usd, then the lower "
    "elapsed_seconds, then the lexicographically smaller model_id."
)
QUALITY_TASK_FIT_RULE = (
    "Quality/task-fit selects the higher risky_recall (missing values sort last), "
    "then the higher requirement_mapping_macro_f1, then the higher "
    "classification_macro_f1, then the lower elapsed_seconds, then the "
    "lexicographically smaller model_id."
)


def parse_model_names(raw: str) -> list[str]:
    """Parse a comma-separated ``--models`` value into unique known names."""

    names = [part.strip() for part in raw.split(",")]
    if any(not name for name in names):
        raise CompareIncompleteError("model names must be non-empty")
    if len(names) < 2:
        raise CompareIncompleteError("compare requires at least two models")
    if len(set(names)) != len(names):
        raise CompareIncompleteError("model names must be unique")
    unknown = [name for name in names if name not in KNOWN_COMPARE_MODELS]
    if unknown:
        raise CompareIncompleteError(
            "unknown model name(s): "
            + ", ".join(unknown)
            + f"; known names: {', '.join(KNOWN_COMPARE_MODELS)}"
        )
    return names


def estimated_cost_usd(model_key: str, token_upper_bound: int) -> float:
    """Return list-price estimate; unknown names fail closed."""

    if model_key not in LIST_PRICE_USD_PER_MILLION_INPUT_TOKENS:
        raise CompareIncompleteError(
            f"no published list price for model {model_key}; unknown names fail closed"
        )
    price = LIST_PRICE_USD_PER_MILLION_INPUT_TOKENS[model_key]
    return price * token_upper_bound / 1_000_000.0


def build_named_gateway(name: str, bundle: EvaluationBundle) -> ModelGateway:
    """Construct a CLI-known deterministic gateway for one comparison slot."""

    if name == "fixture":
        return FixtureModelGateway(name="fixture")
    if name == "fixture-b":
        claims = segment_claims(bundle.generated_output.markdown)
        if bundle.expected_claims:
            text_by_id = {claim.id: claim.text for claim in claims}
            rules = {
                text_by_id[item.claim_id]: item.label
                for item in bundle.expected_claims
                if item.claim_id in text_by_id
            }
        else:
            rules = {claim.text: SupportLabel.SUPPORTED for claim in claims}
        return FixtureModelGateway(name="fixture-b", rules=rules)
    raise CompareIncompleteError(
        f"unknown model name: {name}; known names: {', '.join(KNOWN_COMPARE_MODELS)}"
    )


def _higher_is_better(value: float | None) -> tuple[int, float]:
    if value is None:
        return (1, 0.0)
    return (0, -value)


def quality_task_fit_sort_key(row: ComparedModelResult) -> tuple:
    return (
        _higher_is_better(row.risky_recall),
        _higher_is_better(row.requirement_mapping_macro_f1),
        _higher_is_better(row.classification_macro_f1),
        row.elapsed_seconds,
        row.model_id,
    )


def min_cost_sort_key(row: ComparedModelResult) -> tuple:
    return (row.estimated_cost_usd, row.elapsed_seconds, row.model_id)


def _label_metrics_complete(row: ComparedModelResult) -> bool:
    return (
        row.risky_recall is not None
        and row.requirement_mapping_macro_f1 is not None
        and row.classification_macro_f1 is not None
    )


def _format_optional(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.6f}"


def render_compare_markdown(report: ComparisonReport) -> str:
    lines = [
        "# Model comparison",
        "",
        f"- Bundle: `{report.bundle_id}`",
        f"- Status: `{report.status}`",
        f"- Input SHA-256: `{report.input_sha256}`",
        f"- Comparison wall-clock (seconds): `{report.elapsed_seconds:.6f}`",
        f"- Label verification available: `{report.label_verification_available}`",
        "",
        "Quality, task fit, elapsed time, and estimated cost are reported",
        "separately. They are not combined into one effectiveness index.",
        "Human review remains the only automated success state",
        "(`READY_FOR_HUMAN_REVIEW`). This comparison does not treat the",
        "quality/task-fit rule as a deployment verdict.",
        "",
        "Estimated cost is published list price (USD per million input tokens)",
        "times the conservative UTF-8 byte token upper bound. It is not a bill.",
        "Named `fixture` / `fixture-v1` cost is 0. `fixture-b` uses a small",
        "published mock list price so min-cost and quality can diverge.",
        "",
        "## Models",
        "",
        "| model_id | gateway | run_id | classification_macro_f1 | risky_recall | "
        "risky_precision | mapping_macro_f1 | requirement_coverage | "
        "elapsed_seconds | estimated_cost_usd |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report.models:
        lines.append(
            f"| `{row.model_id}` | `{row.gateway}` | `{row.run_id}` | "
            f"{_format_optional(row.classification_macro_f1)} | "
            f"{_format_optional(row.risky_recall)} | "
            f"{_format_optional(row.risky_precision)} | "
            f"{_format_optional(row.requirement_mapping_macro_f1)} | "
            f"{row.requirement_coverage:.6f} | "
            f"{row.elapsed_seconds:.6f} | "
            f"{row.estimated_cost_usd:.8f} |"
        )
    lines.extend(
        [
            "",
            "## Selection results",
            "",
            f"**Min-cost.** {report.min_cost.rule}",
            f"Selected model: `{report.min_cost.selected_model_id}`.",
            f"classification_macro_f1: {_format_optional(report.min_cost.classification_macro_f1)}; "
            f"risky_recall: {_format_optional(report.min_cost.risky_recall)}.",
            "",
            f"**Quality/task-fit.** {report.quality_task_fit.rule}",
            f"Selected model: `{report.quality_task_fit.selected_model_id}`.",
            f"classification_macro_f1: {_format_optional(report.quality_task_fit.classification_macro_f1)}; "
            f"risky_recall: {_format_optional(report.quality_task_fit.risky_recall)}.",
            "",
        ]
    )
    if report.label_verification_available:
        lines.extend(
            [
                "## Label verification",
                "",
                "Complete `expected_claims` were supplied. Annotation-preferred uses",
                "the same ranking keys as the quality/task-fit rule.",
                f"Annotation-preferred model: `{report.annotation_preferred_model_id}`.",
                "Min-cost matches annotation-preferred: "
                f"`{report.min_cost.matches_annotation_preferred}`.",
                "Quality/task-fit matches annotation-preferred: "
                f"`{report.quality_task_fit.matches_annotation_preferred}`.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Label verification",
                "",
                "Label verification is not available. This run is a comparison only.",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


class ComparisonService:
    """Sequentially evaluate the same bundle under named gateways."""

    def __init__(
        self,
        runs_dir: Path | str = "runs",
        gateways: Mapping[str, ModelGateway] | None = None,
        config: EngineConfig | None = None,
    ) -> None:
        self.runs_dir = Path(runs_dir)
        self._gateways = dict(gateways) if gateways is not None else None
        self.config = config or EngineConfig()

    def compare(self, bundle: EvaluationBundle, model_ids: Sequence[str]) -> ComparisonReport:
        ids = list(model_ids)
        if len(ids) < 2:
            raise CompareIncompleteError("compare requires at least two models")
        if len(set(ids)) != len(ids):
            raise CompareIncompleteError("model names must be unique")
        if any(not item for item in ids):
            raise CompareIncompleteError("model names must be non-empty")
        gateways = self._resolve_gateways(bundle, ids)
        token_bound = conservative_token_upper_bound(bundle)
        rows: list[ComparedModelResult] = []
        input_sha256: str | None = None
        started = time.perf_counter()
        try:
            for model_id in ids:
                gateway = gateways[model_id]
                model_started = time.perf_counter()
                report = EvaluationService(
                    runs_dir=self.runs_dir,
                    gateway=gateway,
                    config=self.config,
                ).evaluate(bundle)
                elapsed = time.perf_counter() - model_started
                if input_sha256 is None:
                    input_sha256 = report.input_sha256
                elif input_sha256 != report.input_sha256:
                    raise CompareIncompleteError(
                        "comparison incomplete because model runs used different inputs"
                    )
                rows.append(_row_from_run(model_id, gateway, report, elapsed, token_bound))
        except CompareIncompleteError:
            raise
        except EvidenceInspectorError as exc:
            raise CompareIncompleteError(
                f"comparison incomplete because a model failed: {exc}"
            ) from exc
        wall = time.perf_counter() - started
        if input_sha256 is None:
            raise CompareIncompleteError("comparison incomplete because no model succeeded")
        comparison = _build_report(bundle, rows, wall, input_sha256)
        _write_compare_artifacts(self.runs_dir, comparison)
        return comparison

    def _resolve_gateways(
        self,
        bundle: EvaluationBundle,
        model_ids: list[str],
    ) -> dict[str, ModelGateway]:
        if self._gateways is not None:
            missing = [name for name in model_ids if name not in self._gateways]
            if missing:
                raise CompareIncompleteError(
                    "unknown model name(s): " + ", ".join(missing)
                )
            return {name: self._gateways[name] for name in model_ids}
        return {name: build_named_gateway(name, bundle) for name in model_ids}


def _row_from_run(
    model_id: str,
    gateway: ModelGateway,
    report: RunReport,
    elapsed_seconds: float,
    token_bound: int,
) -> ComparedModelResult:
    metrics = report.metrics
    return ComparedModelResult(
        model_id=model_id,
        gateway=gateway.name,
        run_id=report.run_id,
        classification_macro_f1=metrics.classification_macro_f1,
        risky_recall=metrics.risky_recall,
        risky_precision=metrics.risky_precision,
        requirement_mapping_macro_f1=metrics.requirement_mapping_macro_f1,
        requirement_coverage=metrics.requirement_coverage,
        elapsed_seconds=elapsed_seconds,
        estimated_cost_usd=estimated_cost_usd(gateway.name, token_bound),
    )


def _selection(
    policy: str,
    row: ComparedModelResult,
    rule: str,
    annotation_preferred: str | None,
) -> SelectionResult:
    matches: bool | None = None
    if annotation_preferred is not None:
        matches = row.model_id == annotation_preferred
    return SelectionResult(
        policy=policy,
        selected_model_id=row.model_id,
        rule=rule,
        matches_annotation_preferred=matches,
        classification_macro_f1=row.classification_macro_f1,
        risky_recall=row.risky_recall,
    )


def _build_report(
    bundle: EvaluationBundle,
    rows: list[ComparedModelResult],
    elapsed_seconds: float,
    input_sha256: str,
) -> ComparisonReport:
    min_cost_row = min(rows, key=min_cost_sort_key)
    quality_row = min(rows, key=quality_task_fit_sort_key)
    label_verification_available = all(_label_metrics_complete(row) for row in rows)
    annotation_preferred_id = (
        quality_row.model_id if label_verification_available else None
    )
    return ComparisonReport(
        bundle_id=bundle.bundle_id,
        input_sha256=input_sha256,
        elapsed_seconds=elapsed_seconds,
        models=rows,
        min_cost=_selection("min_cost", min_cost_row, MIN_COST_RULE, annotation_preferred_id),
        quality_task_fit=_selection(
            "quality_task_fit",
            quality_row,
            QUALITY_TASK_FIT_RULE,
            annotation_preferred_id,
        ),
        label_verification_available=label_verification_available,
        annotation_preferred_model_id=annotation_preferred_id,
        status="READY_FOR_HUMAN_REVIEW",
    )


def _write_compare_artifacts(runs_dir: Path, report: ComparisonReport) -> None:
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "compare.json").write_text(
        report.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    (runs_dir / "compare.md").write_text(render_compare_markdown(report), encoding="utf-8")
