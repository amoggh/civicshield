"""
FastAPI router for triggering and inspecting the LangGraph workflow.
"""

from datetime import datetime, timezone
import logging

from fastapi import APIRouter

from .graph import civicshield_workflow
from .state import (
    CivicShieldState,
    WorkflowRunRequest,
    WorkflowRunResponse,
)

logger = logging.getLogger("civicshield.workflow.router")
router = APIRouter(prefix="/workflow", tags=["LangGraph Workflow"])


@router.post("/run", response_model=WorkflowRunResponse)
def run_incident_response_workflow(req: WorkflowRunRequest):
    """
    Execute the stateful LangGraph incident response workflow:
    Intake -> Diagnose -> Plan -> Safety Gate -> Execute -> Verify -> (Retry / Escalate / Success)
    """
    initial_state: CivicShieldState = {
        "incident_description": req.incident_description,
        "force_fallback": req.force_fallback,
        "attempt_count": 1,
        "max_attempts": req.max_attempts,
        "timeline": [],
    }

    logger.info("Starting LangGraph workflow run: %s", req.incident_description)
    final_state = civicshield_workflow.invoke(initial_state)

    status = final_state.get("status", "COMPLETED")
    if final_state.get("verification_result") and final_state["verification_result"].verified:
        status = "SUCCESS"

    return WorkflowRunResponse(
        status=status,
        incident_description=final_state.get("incident_description", req.incident_description),
        attempt_count=final_state.get("attempt_count", 1),
        hypothesis=final_state.get("hypothesis", ""),
        planner_recommendation=final_state.get("planner_recommendation"),
        governor_decision=final_state.get("governor_decision"),
        execution_result=final_state.get("execution_result"),
        verification_result=final_state.get("verification_result"),
        timeline=final_state.get("timeline", []),
        completed_at=datetime.now(timezone.utc),
    )


@router.get("/mermaid")
def get_workflow_mermaid_diagram():
    """Return the Mermaid graph definition of the LangGraph workflow."""
    return {"mermaid": civicshield_workflow.get_graph().draw_mermaid()}

