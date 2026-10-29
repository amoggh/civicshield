"""
Conditional edge routing logic for the CivicShield LangGraph workflow.

Controls deterministic branching across:
- Plan -> Diagnose (gather more evidence) / Safety Gate (evaluate action) / Escalate / End
- Safety Gate -> Execute (approved) / Escalate (rejected/unsafe)
- Verify -> End (passed) / Diagnose (retry if attempt <= 3) / Escalate (retries exhausted)
"""

import logging

from app.agent.models import PlannerDecisionType

from .state import CivicShieldState

logger = logging.getLogger("civicshield.workflow.edges")


def route_after_plan(state: CivicShieldState) -> str:
    """
    Branching after planning:
    - INVESTIGATE -> re-diagnose with selected tool
    - RECOVER -> safety gate evaluation
    - ESCALATE -> human escalation
    - NO_ACTION -> workflow end (already healthy)
    """
    rec = state.get("planner_recommendation")
    if not rec:
        logger.warning("Routing after plan: Missing planner recommendation -> escalating.")
        return "escalate"

    decision = rec.decision_type
    logger.info("Routing after plan: Decision is '%s'", decision.value)

    if decision == PlannerDecisionType.INVESTIGATE:
        return "diagnose"
    elif decision == PlannerDecisionType.RECOVER:
        return "safety_gate"
    elif decision == PlannerDecisionType.ESCALATE:
        return "escalate"
    elif decision == PlannerDecisionType.NO_ACTION:
        return "end"

    return "escalate"


def route_after_safety(state: CivicShieldState) -> str:
    """
    Branching after deterministic safety governor check:
    - APPROVED -> proceed to execute recovery action
    - REJECTED -> route directly to escalation (unsafe action blocked)
    """
    decision = state.get("governor_decision")
    if not decision:
        logger.warning("Routing after safety: No governor decision found -> escalating.")
        return "escalate"

    if decision.approved:
        logger.info("Routing after safety: Action '%s' APPROVED -> executing.", decision.action_type)
        return "execute"
    else:
        logger.warning("Routing after safety: Action '%s' REJECTED -> escalating.", decision.action_type)
        return "escalate"


def route_after_verify(state: CivicShieldState) -> str:
    """
    Branching after post-repair verification probe:
    - VERIFIED PASSED -> workflow complete (SUCCESS)
    - VERIFIED FAILED and attempt <= max_attempts -> retry loop (re-diagnose)
    - VERIFIED FAILED and attempt > max_attempts -> retries exhausted (escalate)
    """
    verif = state.get("verification_result")
    attempt = state.get("attempt_count", 1)
    max_att = state.get("max_attempts", 3)

    if not verif:
        logger.warning("Routing after verify: No verification result found -> escalating.")
        return "escalate"

    if verif.verified:
        logger.info("Routing after verify: Verification PASSED -> workflow SUCCESS.")
        return "end"

    # Verification failed: check bounded retry threshold
    if attempt <= max_att:
        logger.info(
            "Routing after verify: Verification FAILED. Retrying (attempt %d of %d) -> diagnose.",
            attempt,
            max_att,
        )
        return "diagnose"
    else:
        logger.warning(
            "Routing after verify: Verification FAILED and retry limit (%d) exhausted -> escalate.",
            max_att,
        )
        return "escalate"

