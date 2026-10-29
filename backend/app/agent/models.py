"""
Pydantic models for the LLM Investigator and Repair Planner.

Defines typed schemas for agent recommendations, diagnostic tool selections,
and recovery action proposals. These schemas constrain the model output.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PlannerDecisionType(str, Enum):
    """The high-level intent of the planner."""
    INVESTIGATE = "INVESTIGATE"   # Request more diagnostic tools to gather evidence
    RECOVER = "RECOVER"           # Ready to propose an allowlisted recovery action
    ESCALATE = "ESCALATE"         # Unable to resolve safely; alert human operator
    NO_ACTION = "NO_ACTION"       # System is already healthy


class DiagnosticToolName(str, Enum):
    """The fixed, closed set of diagnostic tools available to the investigator."""
    CHECK_SERVICE_HEALTH = "check_service_health"
    GET_RECENT_LOGS = "get_recent_logs"
    CHECK_DATABASE_STATUS = "check_database_status"
    COMPARE_CONFIGURATION = "compare_configuration"
    MEASURE_LATENCY = "measure_latency"


class PlannerRecommendation(BaseModel):
    """
    Structured output produced by the LLM or Fallback Planner.
    Strictly validated by Pydantic — free-form text hallucinations are rejected.
    """
    decision_type: PlannerDecisionType = Field(
        description="Whether to run another diagnostic tool, propose recovery, or escalate"
    )
    diagnostic_tool: DiagnosticToolName | None = Field(
        default=None,
        description="Tool to run next if decision_type is INVESTIGATE (must be from fixed set)",
    )
    recovery_action: str | None = Field(
        default=None,
        description="Proposed recovery action if decision_type is RECOVER (must be allowlisted)",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the selected tool or recovery action",
    )
    hypothesis: str = Field(
        description="Human-readable hypothesis of what is happening based on evidence",
        min_length=1,
        max_length=500,
    )
    rationale: str = Field(
        description="Step-by-step reasoning grounded strictly in observed evidence",
        min_length=1,
        max_length=500,
    )
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="List of observed diagnostic evidence items supporting this recommendation",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0",
    )
    source: str = Field(
        default="DETERMINISTIC_FALLBACK",
        description="Origin of this plan: GEMINI_MODEL or DETERMINISTIC_FALLBACK",
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when this recommendation was produced",
    )


class AgentStatusResponse(BaseModel):
    """Runtime configuration status of the AI agent."""
    has_api_key: bool
    model_name: str
    active_mode: str  # "LLM_ONLINE" or "DETERMINISTIC_FALLBACK"
    available_diagnostic_tools: list[str]
    allowed_recovery_actions: list[str]
