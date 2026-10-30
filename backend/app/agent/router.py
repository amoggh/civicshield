"""
FastAPI router for the AI Investigator, Diagnostic Analyst, and Recovery Planner.
"""

from fastapi import APIRouter, Query

from app.diagnostics.models import DiagnosticReport
from app.diagnostics.tools import run_all_diagnostics

from .analyst import diagnostic_analyst
from .models import AgentStatusResponse, DiagnosticAnalysis, PlannerRecommendation
from .planner import investigation_planner

router = APIRouter(prefix="/agent", tags=["AI Investigator & Planner"])


@router.post("/analyze", response_model=DiagnosticAnalysis)
def generate_diagnostic_analysis(
    force_fallback: bool = Query(
        default=False,
        description="Force the deterministic rule analyst even if an API key is present",
    ),
):
    """
    Run the Diagnostic Analyst to analyze current diagnostic telemetry
    and produce a structured root-cause diagnosis.
    """
    report: DiagnosticReport = run_all_diagnostics()
    return diagnostic_analyst.analyze(report=report, force_fallback=force_fallback)


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
    analysis: DiagnosticAnalysis = diagnostic_analyst.analyze(report=report, force_fallback=force_fallback)
    return investigation_planner.plan(report=report, analysis=analysis, force_fallback=force_fallback)


@router.get("/status", response_model=AgentStatusResponse)
def get_agent_status():
    """Retrieve runtime configuration, model availability, and tool/action lists."""
    return investigation_planner.get_status()
