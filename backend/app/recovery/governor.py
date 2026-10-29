"""
Deterministic Safety Governor for CivicShield.

Enforces four strict validation gates before any proposed action can execute:
1. Attempt Limit Gate: Max 3 recovery attempts per incident.
2. Allowlist Gate: Action type must be explicitly in the safe allowlist.
3. Parameter Gate: Rejects dangerous flags, shell commands, or unexpected parameters.
4. Evidence Requirement Gate: Action must be justified by documented diagnostic evidence.

Never relies on LLM self-policing; all checks are deterministic Python code.
"""

from datetime import datetime, timezone
import re

from .models import (
    ALLOWED_RECOVERY_ACTIONS,
    MAX_RECOVERY_ATTEMPTS,
    ActionProposal,
    GovernorDecision,
    RecoveryActionType,
)

# Forbidden parameter keywords or patterns that indicate dangerous intent
DANGEROUS_PARAM_KEYWORDS = {
    "drop",
    "delete",
    "truncate",
    "rm",
    "remove",
    "shell",
    "exec",
    "eval",
    "bypass",
    "force",
    "cascade",
    "all",
    "kill",
}

# Mapping of allowlisted actions to expected evidence indicators
REQUIRED_EVIDENCE_MAP = {
    RecoveryActionType.RESTORE_BASELINE_CONFIG.value: {
        "config_divergence",
        "unknown_host",
        "config_error",
        "configuration",
    },
    RecoveryActionType.RECONNECT_DATABASE.value: {
        "db_unavailable",
        "connection_refused",
        "database_down",
        "database",
    },
    RecoveryActionType.CLEAR_LATENCY_DELAY.value: {
        "high_latency",
        "latency_violation",
        "timeout",
        "sla_breach",
    },
    RecoveryActionType.RESTART_SERVICE.value: {
        "service_down",
        "service_degraded",
        "system_unresponsive",
        "general_failure",
    },
}


def validate_recovery_proposal(proposal: ActionProposal) -> GovernorDecision:
    """
    Evaluate an action proposal against deterministic safety rules.
    Returns a GovernorDecision approving or rejecting the proposal.
    """
    now = datetime.now(timezone.utc)

    # Gate 1: Bounded Retry Limit
    if proposal.attempt_number > MAX_RECOVERY_ATTEMPTS:
        return GovernorDecision(
            approved=False,
            action_type=proposal.action_type,
            attempt_number=proposal.attempt_number,
            reason=(
                f"Maximum recovery attempts ({MAX_RECOVERY_ATTEMPTS}) exceeded. "
                "Halting automated recovery and escalating to human administrator."
            ),
            requires_human_escalation=True,
            timestamp=now,
        )

    # Gate 2: Action Name Allowlist
    if proposal.action_type not in ALLOWED_RECOVERY_ACTIONS:
        return GovernorDecision(
            approved=False,
            action_type=proposal.action_type,
            attempt_number=proposal.attempt_number,
            reason=(
                f"Action '{proposal.action_type}' is FORBIDDEN by safety policy. "
                f"Only pre-approved actions may execute: {sorted(ALLOWED_RECOVERY_ACTIONS)}"
            ),
            requires_human_escalation=True,
            timestamp=now,
        )

    # Gate 3: Parameter Safety & Non-destructiveness
    for param_key, param_value in proposal.parameters.items():
        key_lower = str(param_key).lower()
        val_lower = str(param_value).lower()
        for forbidden in DANGEROUS_PARAM_KEYWORDS:
            if forbidden in key_lower or forbidden in val_lower:
                return GovernorDecision(
                    approved=False,
                    action_type=proposal.action_type,
                    attempt_number=proposal.attempt_number,
                    reason=(
                        f"Action '{proposal.action_type}' contains dangerous parameter "
                        f"'{param_key}={param_value}'. Execution rejected."
                    ),
                    requires_human_escalation=True,
                    timestamp=now,
                )

    # Gate 4: Evidence Justification
    if not proposal.supporting_evidence:
        return GovernorDecision(
            approved=False,
            action_type=proposal.action_type,
            attempt_number=proposal.attempt_number,
            reason=(
                f"Action '{proposal.action_type}' rejected: No supporting diagnostic evidence provided. "
                "Actions must be grounded in observed diagnostic facts."
            ),
            requires_human_escalation=False,
            timestamp=now,
        )

    expected_evidence = REQUIRED_EVIDENCE_MAP.get(proposal.action_type, set())
    evidence_tokens = {
        re.sub(r"[^a-z0-9_]", "", token.lower())
        for token in proposal.supporting_evidence
    }

    # Verify at least one piece of evidence correlates with the proposed recovery
    has_correlation = any(
        any(exp in token or token in exp for exp in expected_evidence)
        for token in evidence_tokens
    )

    if not has_correlation:
        return GovernorDecision(
            approved=False,
            action_type=proposal.action_type,
            attempt_number=proposal.attempt_number,
            reason=(
                f"Action '{proposal.action_type}' does not address the supplied diagnostic evidence: "
                f"{proposal.supporting_evidence}. Expected evidence related to {sorted(expected_evidence)}."
            ),
            requires_human_escalation=False,
            timestamp=now,
        )

    # All gates passed
    return GovernorDecision(
        approved=True,
        action_type=proposal.action_type,
        attempt_number=proposal.attempt_number,
        reason=(
            f"Action '{proposal.action_type}' passed all deterministic safety checks "
            f"(allowlist, parameters, evidence justification, attempt #{proposal.attempt_number})."
        ),
        requires_human_escalation=False,
        timestamp=now,
    )

