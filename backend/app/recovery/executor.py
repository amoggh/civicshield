"""
Simulated recovery action executor.

Executes only allowlisted recovery actions that have passed safety governor validation.
Modifies only the in-memory simulator state.
"""

from datetime import datetime, timezone
import logging

from app.clinic.service import clinic
from app.simulator.config import reset_active_config
from app.simulator.faults import fault_manager
from app.simulator.models import FaultType

from .models import (
    ActionProposal,
    ExecutionResult,
    GovernorDecision,
    RecoveryActionType,
)

logger = logging.getLogger("civicshield.recovery.executor")


def execute_recovery_action(
    decision: GovernorDecision,
    proposal: ActionProposal,
) -> ExecutionResult:
    """
    Execute an approved recovery action against the local simulator.
    Raises ValueError if called with an unapproved decision.
    """
    now = datetime.now(timezone.utc)

    if not decision.approved:
        raise ValueError(
            f"Execution rejected: Safety Governor denied action '{proposal.action_type}': {decision.reason}"
        )

    action = proposal.action_type

    if action == RecoveryActionType.RESTORE_BASELINE_CONFIG.value:
        reset_active_config()
        if FaultType.INVALID_DB_CONFIG in fault_manager.active_faults:
            fault_manager.active_faults.remove(FaultType.INVALID_DB_CONFIG)
            fault_manager.fault_details.pop(FaultType.INVALID_DB_CONFIG, None)
        clinic._log_event("REPAIR_APPLIED", "Restored golden baseline configuration")
        msg = "Restored golden baseline configuration (127.0.0.1:5432). Config drift eliminated."

    elif action == RecoveryActionType.RECONNECT_DATABASE.value:
        if FaultType.DB_UNAVAILABLE in fault_manager.active_faults:
            fault_manager.active_faults.remove(FaultType.DB_UNAVAILABLE)
            fault_manager.fault_details.pop(FaultType.DB_UNAVAILABLE, None)
        clinic._log_event("REPAIR_APPLIED", "Simulated database connection restored")
        msg = "Reconnected simulated database socket on port 5432."

    elif action == RecoveryActionType.CLEAR_LATENCY_DELAY.value:
        if FaultType.HIGH_LATENCY in fault_manager.active_faults:
            fault_manager.active_faults.remove(FaultType.HIGH_LATENCY)
            fault_manager.fault_details.pop(FaultType.HIGH_LATENCY, None)
        clinic._log_event("REPAIR_APPLIED", "Simulated latency overhead cleared")
        msg = "Simulated latency delay cleared; response times restored to normal."

    elif action == RecoveryActionType.RESTART_SERVICE.value:
        fault_manager.reset()
        clinic.status = clinic.status.HEALTHY
        clinic._log_event("SERVICE_RESTART", "Service restarted; baseline state reloaded")
        msg = "Simulated service restart completed. All components reinitialized."

    else:
        raise ValueError(f"Unimplemented allowlisted action '{action}'")

    logger.info("Successfully executed recovery action: %s", action)
    return ExecutionResult(
        executed=True,
        action_type=action,
        message=msg,
        timestamp=now,
    )

