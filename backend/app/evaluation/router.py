"""
FastAPI router for running and retrieving benchmark evaluation results.
"""

from fastapi import APIRouter

from .models import EvaluationReport
from .runner import evaluation_runner

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmark"])


@router.post("/run", response_model=EvaluationReport)
def run_benchmark_evaluation():
    """
    Execute repeatable benchmark suite comparing CivicShield vs RestartBaseline
    across all synthetic scenarios. Calculates empirical metrics and persists results.
    """
    return evaluation_runner.run_benchmark()


@router.get("/results", response_model=EvaluationReport)
def get_latest_benchmark_results():
    """Retrieve the latest recorded benchmark evaluation report."""
    return evaluation_runner.get_latest_results()

