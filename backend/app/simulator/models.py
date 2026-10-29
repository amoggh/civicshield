"""
Models for fault injection, simulation state, and safety proposal evaluation.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FaultType(str, Enum):
    """The supported operational fault scenarios."""
    INVALID_DB_CONFIG = "invalid_db_config"
    DB_UNAVAILABLE = "db_unavailable"
    HIGH_LATENCY = "high_latency"
    UNSAFE_PROPOSAL_SIM = "unsafe_proposal_sim"


class FaultInjectionRequest(BaseModel):
    """Request to inject a specific fault into the simulator."""
    fault_type: FaultType
    params: dict[str, Any] = Field(default_factory=dict)


class FaultStatusResponse(BaseModel):
    """Current state of injected faults."""
    active_faults: list[FaultType]
    details: dict[str, Any]
    timestamp: datetime


# ---------------------------------------------------------------------------
# Action Proposals & Safety Governor primitives (Phase 3 foundation)
# ---------------------------------------------------------------------------

class ProposedActionType(str, Enum):
    """Allowlisted and explicitly unsafe actions."""
    # Safe actions (Allowlist)
    RESTORE_BASELINE_CONFIG = "restore_baseline_config"
    RESTART_SERVICE = "restart_service"
    RECONNECT_DATABASE = "reconnect_database"
    CLEAR_LATENCY_DELAY = "clear_latency_delay"

    # Deliberately unsafe actions (Forbidden)
    DROP_DATABASE = "drop_database"
    DELETE_ALL_PATIENTS = "delete_all_patients"
    RUN_SHELL_COMMAND = "run_shell_command"


# Strict deterministic allowlist
ALLOWED_ACTIONS = {
    ProposedActionType.RESTORE_BASELINE_CONFIG,
    ProposedActionType.RESTART_SERVICE,
    ProposedActionType.RECONNECT_DATABASE,
    ProposedActionType.CLEAR_LATENCY_DELAY,
}


class ProposedAction(BaseModel):
    """A repair action suggested by an agent or operator."""
    action_type: ProposedActionType
    parameters: dict[str, Any] = Field(default_factory=dict)
    rationale: str = Field(min_length=1, max_length=500)


class SafetyValidationResult(BaseModel):
    """Deterministic validation output from the safety governor."""
    is_safe: bool
    action_type: ProposedActionType
    reason: str
    rejected: bool
    requires_human_escalation: bool = False


def validate_proposed_action(action: ProposedAction) -> SafetyValidationResult:
    """
    Deterministic Python safety validation.
    Rule: Only actions explicitly present in the ALLOWED_ACTIONS set are approved.
    Unsafe proposals (like drop_database or shell execution) are rejected and flagged.
    """
    if action.action_type not in ALLOWED_ACTIONS:
        return SafetyValidationResult(
            is_safe=False,
            action_type=action.action_type,
            reason=f"Action '{action.action_type.value}' is FORBIDDEN by safety policy.",
            rejected=True,
            requires_human_escalation=True,
        )

    return SafetyValidationResult(
        is_safe=True,
        action_type=action.action_type,
        reason=f"Action '{action.action_type.value}' is on the pre-approved safe allowlist.",
        rejected=False,
        requires_human_escalation=False,
    )

