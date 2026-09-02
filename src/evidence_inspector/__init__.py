"""Model Effectiveness Evaluation Workbench (Inspector engine)."""

from .compare import ComparisonService
from .engine import EvaluationService
from .schemas import ComparisonReport, EvaluationBundle, RunReport

__all__ = [
    "ComparisonReport",
    "ComparisonService",
    "EvaluationBundle",
    "EvaluationService",
    "RunReport",
]
__version__ = "0.1.0"

