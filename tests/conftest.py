from __future__ import annotations

from pathlib import Path

import pytest

from evidence_inspector.schemas import EvaluationBundle


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def sample_bundle() -> EvaluationBundle:
    return EvaluationBundle.model_validate_json(
        (PROJECT_ROOT / "examples" / "sample_bundle.json").read_text(encoding="utf-8")
    )

