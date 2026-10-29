"""
FastAPI router for the AI Investigator and Repair Planner.
"""

from fastapi import APIRouter, Query

from app.diagnostics.models import DiagnosticReport
from app.diagnostics.tools import run_all_diagnostics

from .models import AgentStatusResponse, PlannerRecommendation
from .planner import investigation_planner

router = APIRouter(prefix="/agent", tags=["AI Investigator & Planner"])


@router.post("/plan", response_model=PlannerRecommendation)
def generate_investigation_plan(
    force_fallback: bool = Query(
        default=False,
        description="Force the deterministic rule planner even if an API key is present",
    ),
):
    """
    Generate an investigation plan or recovery recommendation based on current diagnostic evidence.
    Uses Gemini when configured; otherwise runs the deterministic fallback engine.
    """
    report: DiagnosticReport = run_all_diagnostics()
    return investigation_planner.plan(report=report, force_fallback=force_fallback)


@router.get("/status", response_model=AgentStatusResponse)
def get_agent_status():
    """Retrieve runtime configuration, model availability, and tool/action lists."""
    return investigation_planner.get_status()

