"""
Conditional edge routing logic for the CivicShield LangGraph workflow.

Controls deterministic branching across:
- Plan -> Diagnose (gather more evidence) / Safety Gate (evaluate action) / Escalate / End
- Safety Gate -> Execute (approved) / Escalate (rejected/unsafe) / Shadow / Await Approval
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
    - If Governor REJECTED -> route directly to escalate (unsafe action blocked)
    - If Governor APPROVED:
      - If autonomy_mode == 'shadow' -> route to shadow evaluation
      - If autonomy_mode == 'supervised' ->
        - if human_approved is None -> route to await_approval (pause)
        - if human_approved is True -> route to execute
        - if human_approved is False -> route to escalate
      - If autonomy_mode == 'autonomous' -> route to execute
    """
    decision = state.get("governor_decision")
    if not decision:
        logger.warning("Routing after safety: No governor decision found -> escalating.")
        return "escalate"

    if not decision.approved:
        logger.warning("Routing after safety: Action '%s' REJECTED by Governor -> escalating.", decision.action_type)
        return "escalate"

    autonomy_mode = state.get("autonomy_mode", "autonomous")

    if autonomy_mode == "shadow":
        logger.info("Routing after safety: Shadow Mode active -> routing to shadow evaluation.")
        return "shadow"
    elif autonomy_mode == "supervised":
        human_approved = state.get("human_approved")
        if human_approved is None:
            logger.info("Routing after safety: Supervised Mode active -> awaiting human approval.")
            return "await_approval"
        elif human_approved is True:
            logger.info("Routing after safety: Human operator approved action -> executing.")
            return "execute"
        else:
            logger.warning("Routing after safety: Human operator rejected action -> escalating.")
            return "escalate"
    else:
        logger.info("Routing after safety: Autonomous Mode active -> executing.")
        return "execute"


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
