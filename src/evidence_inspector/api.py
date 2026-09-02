"""FastAPI surface for the same service used by the CLI."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from fastapi import FastAPI, HTTPException, Path as ApiPath, status
from pydantic import BaseModel, ConfigDict

from .engine import EvaluationService
from .errors import EvidenceInspectorError, ProviderUnavailable, RunNotFound
from .gateway import build_gateway_from_environment
from .schemas import EvaluationBundle, HumanReviewInput, HumanReviewRecord, RunReport


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    version: str


def create_app(
    runs_dir: Path | str | None = None,
    service: EvaluationService | None = None,
    environ: Mapping[str, str] | None = None,
) -> FastAPI:
    if service is None:
        root = runs_dir or os.environ.get("EVIDENCE_INSPECTOR_RUNS", "runs")
        service = EvaluationService(
            runs_dir=root,
            gateway=build_gateway_from_environment(environ),
        )
    app = FastAPI(
        title="Model Effectiveness Evaluation Workbench",
        version="0.1.0",
        description=(
            "Workbench compare shell over the Inspector engine. "
            "Traceable decision support; every evaluation requires human review."
        ),
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", version="0.1.0")

    @app.post(
        "/v1/evaluations",
        response_model=RunReport,
        status_code=status.HTTP_201_CREATED,
    )
    def evaluate(bundle: EvaluationBundle) -> RunReport:
        try:
            return service.evaluate(bundle)
        except ProviderUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except EvidenceInspectorError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/v1/evaluations/{run_id}", response_model=RunReport)
    def get_evaluation(
        run_id: str = ApiPath(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$"),
    ) -> RunReport:
        try:
            return service.get_report(run_id)
        except RunNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except EvidenceInspectorError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/v1/evaluations/{run_id}/reviews",
        response_model=HumanReviewRecord,
        status_code=status.HTTP_201_CREATED,
    )
    def append_review(
        review: HumanReviewInput,
        run_id: str = ApiPath(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$"),
    ) -> HumanReviewRecord:
        try:
            return service.review(run_id, review)
        except RunNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except EvidenceInspectorError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()
