"""
State schema for the CivicShield LangGraph incident response workflow.
Supports Shadow Mode, Supervised Mode, and Autonomous Mode.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, TypedDict

from pydantic import BaseModel, Field

from app.agent.models import DiagnosticAnalysis, PlannerRecommendation
from app.diagnostics.models import DiagnosticReport
from app.recovery.models import (
    ActionProposal,
    ExecutionResult,
    GovernorDecision,
    VerificationResult,
)


class AutonomyMode(str, Enum):
    """The operating autonomy policy for the incident remediation workflow."""
    SHADOW = "shadow"          # Observe and evaluate; strictly never execute repairs
    SUPERVISED = "supervised"  # Pause for explicit human approval before executing
    AUTONOMOUS = "autonomous"  # Automatically execute safe, allowlisted repairs


class ExecutionEvent(BaseModel):
    """
    Detailed telemetry event capturing agent interactions, tool calls, and control flow.
    Enables deep inspection and visualization of multi-agent collaboration.
    """
    event_id: str = Field(description="Unique event ID")
    run_id: str = Field(description="Workflow execution run ID")
    seq: int = Field(description="Monotonically increasing sequence number")
    timestamp: str = Field(description="ISO 8601 UTC timestamp")
    node: str = Field(description="LangGraph workflow node name")
    agent_id: str = Field(description="Identifier for the agent or component (e.g. diagnostic_analyst, recovery_planner, safety_governor)")
    agent_type: str = Field(
        description="Type classification: 'ai_agent' | 'deterministic_guardrail' | 'deterministic_tool' | 'workflow_controller' | 'human_operator'"
    )
    event_type: str = Field(
        description="Event kind: 'node_start' | 'node_complete' | 'agent_handoff' | 'tool_call' | 'safety_evaluation' | 'human_review' | 'workflow_escalate'"
    )
    status: str = Field(
        description="Execution status: 'success' | 'failed' | 'blocked' | 'paused' | 'escalated'"
    )
    input_summary: str = Field(description="Summary of input received by this component")
    output_summary: str = Field(description="Summary of output or decision produced")
    structured_payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Complete typed payload produced for deep inspection",
    )
    handoff_to: str | None = Field(
        default=None,
        description="Target agent or node for state handoff",
    )
    duration_ms: float | None = Field(
        default=None,
        description="Execution time in milliseconds",
    )
    error_detail: str | None = Field(
        default=None,
        description="Error or rejection detail if applicable",
    )


class CivicShieldState(TypedDict, total=False):
    """
    Central state container passed between LangGraph nodes.
    Maintains an immutable record of evidence, hypotheses, decisions, and attempts.
    """
    run_id: str
    incident_description: str
    autonomy_mode: str
    evidence: DiagnosticReport | None
    diagnostic_analysis: DiagnosticAnalysis | None
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
    events: list[ExecutionEvent]
    error_message: str | None
    force_fallback: bool
    awaiting_approval: bool
    human_approved: bool | None
    rejection_reason: str | None
    shadow_matches_expected: bool | None
    shadow_expected_action: str | None


class WorkflowRunRequest(BaseModel):
    """Request payload to initiate an investigation & recovery workflow."""
    incident_description: str = Field(
        default="Automated clinic incident response trigger",
        description="Description of the incident or reported symptom",
    )
    autonomy_mode: AutonomyMode = Field(
        default=AutonomyMode.AUTONOMOUS,
        description="Autonomy mode: 'shadow' (observe only), 'supervised' (human gate), 'autonomous' (auto-execute)",
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


class WorkflowResumeRequest(BaseModel):
    """Request payload for human operator decision in Supervised Mode."""
    approved: bool = Field(
        description="Whether the operator approves executing the proposed repair"
    )
    rejection_reason: str | None = Field(
        default=None,
        description="Optional justification if the proposal is rejected"
    )
    paused_state: dict[str, Any] = Field(
        description="The serialized state dictionary returned when workflow paused in AWAITING_APPROVAL"
    )


class WorkflowRunResponse(BaseModel):
    """Response returned upon workflow completion, pause, or escalation."""
    status: str
    autonomy_mode: str = "autonomous"
    incident_description: str
    attempt_count: int
    hypothesis: str
    diagnostic_analysis: DiagnosticAnalysis | None = None
    planner_recommendation: PlannerRecommendation | None
    proposed_action: ActionProposal | None = None
    governor_decision: GovernorDecision | None
    execution_result: ExecutionResult | None
    verification_result: VerificationResult | None
    timeline: list[dict[str, Any]]
    events: list[ExecutionEvent] = Field(default_factory=list)
    completed_at: datetime
    awaiting_approval: bool = False
    human_approved: bool | None = None
    shadow_matches_expected: bool | None = None
    shadow_expected_action: str | None = None
