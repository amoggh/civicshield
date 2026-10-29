"""
State schema for the CivicShield LangGraph incident response workflow.
"""

from datetime import datetime, timezone
from typing import Any, TypedDict

from pydantic import BaseModel, Field

from app.agent.models import PlannerRecommendation
from app.diagnostics.models import DiagnosticReport
from app.recovery.models import (
    ActionProposal,
    ExecutionResult,
    GovernorDecision,
    VerificationResult,
)


class CivicShieldState(TypedDict, total=False):
    """
    Central state container passed between LangGraph nodes.
    Maintains an immutable record of evidence, hypotheses, decisions, and attempts.
    """
    incident_description: str
    evidence: DiagnosticReport | None
    hypothesis: str
    planner_recommendation: PlannerRecommendation | None
    proposed_action: ActionProposal | None
    governor_decision: GovernorDecision | None
    execution_result: ExecutionResult | None
    verification_result: VerificationResult | None
    attempt_count: int
    max_attempts: int
    status: str
    timeline: list[dict[str, Any]]
    error_message: str | None
    force_fallback: bool


class WorkflowRunRequest(BaseModel):
    """Request payload to initiate an autonomous investigation & recovery workflow."""
    incident_description: str = Field(
        default="Automated clinic incident response trigger",
        description="Description of the incident or reported symptom",
    )
    force_fallback: bool = Field(
        default=False,
        description="Force the deterministic rule planner even if an API key is present",
    )
    max_attempts: int = Field(
        default=3,
        ge=1,
        le=3,
        description="Maximum recovery retry attempts before mandatory escalation",
    )


class WorkflowRunResponse(BaseModel):
    """Response returned upon workflow completion or escalation."""
    status: str
    incident_description: str
    attempt_count: int
    hypothesis: str
    planner_recommendation: PlannerRecommendation | None
    governor_decision: GovernorDecision | None
    execution_result: ExecutionResult | None
    verification_result: VerificationResult | None
    timeline: list[dict[str, Any]]
    completed_at: datetime

