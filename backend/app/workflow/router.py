"""
FastAPI router for triggering, resuming, and inspecting the LangGraph workflow.
Supports Shadow Mode, Supervised Mode (Human-in-the-Loop), and Autonomous Mode.
"""

from datetime import datetime, timezone
import logging

from fastapi import APIRouter

from .graph import civicshield_workflow
from .nodes import resume_supervised_workflow
from .state import (
    CivicShieldState,
    WorkflowResumeRequest,
    WorkflowRunRequest,
    WorkflowRunResponse,
)

logger = logging.getLogger("civicshield.workflow.router")
router = APIRouter(prefix="/workflow", tags=["LangGraph Workflow"])


@router.post("/run", response_model=WorkflowRunResponse)
def run_incident_response_workflow(req: WorkflowRunRequest):
    """
    Execute the stateful LangGraph incident response workflow.
    Supports:
      - 'shadow': Observe & evaluate only; strictly never executes repairs.
      - 'supervised': Pauses after safety approval for human authorization.
      - 'autonomous': Automatically executes allowlisted safe repairs.
    """
    initial_state: CivicShieldState = {
        "incident_description": req.incident_description,
        "autonomy_mode": req.autonomy_mode.value,
        "force_fallback": req.force_fallback,
        "attempt_count": 1,
        "max_attempts": req.max_attempts,
        "timeline": [],
        "awaiting_approval": False,
    }

    logger.info(
        "Starting LangGraph workflow run (mode=%s): %s",
        req.autonomy_mode.value,
        req.incident_description,
    )
    final_state = civicshield_workflow.invoke(initial_state)

    status = final_state.get("status", "COMPLETED")
    if final_state.get("verification_result") and final_state["verification_result"].verified:
        status = "SUCCESS"

    return WorkflowRunResponse(
        status=status,
        autonomy_mode=final_state.get("autonomy_mode", req.autonomy_mode.value),
        incident_description=final_state.get("incident_description", req.incident_description),
        attempt_count=final_state.get("attempt_count", 1),
        hypothesis=final_state.get("hypothesis", ""),
        planner_recommendation=final_state.get("planner_recommendation"),
        proposed_action=final_state.get("proposed_action"),
        governor_decision=final_state.get("governor_decision"),
        execution_result=final_state.get("execution_result"),
        verification_result=final_state.get("verification_result"),
        timeline=final_state.get("timeline", []),
        completed_at=datetime.now(timezone.utc),
        awaiting_approval=final_state.get("awaiting_approval", False),
        human_approved=final_state.get("human_approved"),
        shadow_matches_expected=final_state.get("shadow_matches_expected"),
        shadow_expected_action=final_state.get("shadow_expected_action"),
    )


@router.post("/resume", response_model=WorkflowRunResponse)
def resume_workflow_execution(req: WorkflowResumeRequest):
    """
    Resume execution of a paused Supervised Mode workflow.
    - If approved=True: Executes the approved safe repair and runs verification probe.
    - If approved=False: Escalates with operator's justification, strictly preventing execution.
    """
    logger.info("Resuming supervised workflow (approved=%s, reason=%s)", req.approved, req.rejection_reason)
    resumed_state = resume_supervised_workflow(
        paused_state=req.paused_state,
        approved=req.approved,
        rejection_reason=req.rejection_reason,
    )

    status = resumed_state.get("status", "COMPLETED")
    if resumed_state.get("verification_result") and resumed_state["verification_result"].verified:
        status = "SUCCESS"

    return WorkflowRunResponse(
        status=status,
        autonomy_mode=resumed_state.get("autonomy_mode", "supervised"),
        incident_description=resumed_state.get("incident_description", "Supervised incident response"),
        attempt_count=resumed_state.get("attempt_count", 1),
        hypothesis=resumed_state.get("hypothesis", ""),
        planner_recommendation=resumed_state.get("planner_recommendation"),
        proposed_action=resumed_state.get("proposed_action"),
        governor_decision=resumed_state.get("governor_decision"),
        execution_result=resumed_state.get("execution_result"),
        verification_result=resumed_state.get("verification_result"),
        timeline=resumed_state.get("timeline", []),
        completed_at=datetime.now(timezone.utc),
        awaiting_approval=False,
        human_approved=resumed_state.get("human_approved"),
        shadow_matches_expected=None,
        shadow_expected_action=None,
    )


@router.get("/mermaid")
def get_workflow_mermaid_diagram():
    """Return the Mermaid graph definition of the LangGraph workflow."""
    return {"mermaid": civicshield_workflow.get_graph().draw_mermaid()}
