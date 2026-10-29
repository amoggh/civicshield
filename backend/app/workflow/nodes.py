"""
LangGraph node implementations for CivicShield incident response.

Each node represents a distinct phase of the investigation and recovery lifecycle:
- intake: Records the trigger and initial incident context.
- diagnose: Probes the simulated clinic and collects structured evidence.
- plan: Formulates a hypothesis and selects a recovery action or diagnostic.
- safety_gate: Validates proposed actions against deterministic Python rules.
- execute: Applies safe recovery actions against the simulator.
- verify: Runs post-repair verification checks to prove recovery.
- escalate: Halts automation and requests human operator intervention.
"""

from datetime import datetime, timezone
import logging
from typing import Any

from app.agent.models import PlannerDecisionType
from app.agent.planner import investigation_planner
from app.diagnostics.tools import run_all_diagnostics
from app.recovery.executor import execute_recovery_action
from app.recovery.governor import validate_recovery_proposal
from app.recovery.models import ActionProposal, AuditStage
from app.recovery.timeline import audit_timeline
from app.recovery.verifier import verify_system_recovery

from .state import CivicShieldState

logger = logging.getLogger("civicshield.workflow.nodes")


def _append_timeline_event(
    timeline: list[dict[str, Any]],
    stage: str,
    summary: str,
    details: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Helper to append a structured milestone to the workflow timeline."""
    new_timeline = list(timeline)
    new_timeline.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "summary": summary,
        "details": details or {},
    })
    return new_timeline


def intake_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 1: Intake incident report and initialize workflow state."""
    desc = state.get("incident_description", "Automated incident intake")
    attempt = state.get("attempt_count", 1)
    max_att = state.get("max_attempts", 3)
    timeline = state.get("timeline", [])

    logger.info("Workflow [INTAKE]: %s", desc)

    updated_timeline = _append_timeline_event(
        timeline,
        stage="INTAKE",
        summary=f"Incident ingested: {desc}",
        details={"attempt": attempt, "max_attempts": max_att},
    )

    audit_timeline.record(
        stage=AuditStage.PROPOSED,
        action_type="incident_intake",
        attempt_number=attempt,
        details={"incident": desc},
        success=True,
    )

    return {
        "status": "DIAGNOSING",
        "attempt_count": attempt,
        "max_attempts": max_att,
        "timeline": updated_timeline,
    }


def diagnose_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 2: Execute diagnostic suite and refresh structured evidence."""
    logger.info("Workflow [DIAGNOSE]: Probing clinic health, DB, config, latency...")

    report = run_all_diagnostics()
    timeline = state.get("timeline", [])

    summary = (
        f"Health: {report.service_health.status} | "
        f"DB: {report.database.status_code} | "
        f"Config Divergence: {report.configuration.has_divergence} | "
        f"Latency SLA Violated: {report.latency.sla_violated}"
    )

    updated_timeline = _append_timeline_event(
        timeline,
        stage="DIAGNOSE",
        summary=summary,
        details={
            "status": report.service_health.status,
            "divergent_keys": report.configuration.divergent_keys,
            "avg_latency_ms": report.latency.avg_latency_ms,
            "error_logs_count": report.logs.error_count,
        },
    )

    return {
        "evidence": report,
        "status": "PLANNING",
        "timeline": updated_timeline,
    }


def plan_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 3: Analyze evidence with Gemini/Fallback and formulate recovery proposal."""
    report = state.get("evidence")
    force_fallback = state.get("force_fallback", False)
    attempt = state.get("attempt_count", 1)
    timeline = state.get("timeline", [])

    logger.info("Workflow [PLAN]: Formulating plan (force_fallback=%s, attempt=%d)...", force_fallback, attempt)

    recommendation = investigation_planner.plan(report=report, force_fallback=force_fallback)

    proposed_action = None
    if recommendation.decision_type == PlannerDecisionType.RECOVER and recommendation.recovery_action:
        proposed_action = ActionProposal(
            action_type=recommendation.recovery_action,
            parameters=recommendation.parameters,
            rationale=recommendation.rationale,
            supporting_evidence=recommendation.supporting_evidence,
            attempt_number=attempt,
        )

    updated_timeline = _append_timeline_event(
        timeline,
        stage="PLAN",
        summary=f"Decision: {recommendation.decision_type.value} -> {recommendation.recovery_action or recommendation.diagnostic_tool or 'NONE'}",
        details={
            "hypothesis": recommendation.hypothesis,
            "decision_type": recommendation.decision_type.value,
            "action": recommendation.recovery_action,
            "tool": recommendation.diagnostic_tool.value if recommendation.diagnostic_tool else None,
            "confidence": recommendation.confidence_score,
            "source": recommendation.source,
        },
    )

    return {
        "hypothesis": recommendation.hypothesis,
        "planner_recommendation": recommendation,
        "proposed_action": proposed_action,
        "status": "PLANNING_COMPLETED",
        "timeline": updated_timeline,
    }


def safety_gate_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 4: Deterministic Safety Governor validation."""
    proposal = state.get("proposed_action")
    timeline = state.get("timeline", [])

    if not proposal:
        logger.warning("Workflow [SAFETY_GATE]: No proposed action in state to evaluate.")
        return {"status": "ESCALATED"}

    logger.info("Workflow [SAFETY_GATE]: Validating proposed action '%s'...", proposal.action_type)

    decision = validate_recovery_proposal(proposal)

    updated_timeline = _append_timeline_event(
        timeline,
        stage="SAFETY_CHECK",
        summary=f"Safety Governor: {'APPROVED' if decision.approved else 'REJECTED'}",
        details={
            "action_type": decision.action_type,
            "approved": decision.approved,
            "reason": decision.reason,
            "requires_human_escalation": decision.requires_human_escalation,
        },
    )

    audit_timeline.record(
        stage=AuditStage.SAFETY_CHECK,
        action_type=decision.action_type,
        attempt_number=decision.attempt_number,
        details={"approved": decision.approved, "reason": decision.reason},
        success=decision.approved,
    )

    return {
        "governor_decision": decision,
        "status": "APPROVED" if decision.approved else "REJECTED",
        "timeline": updated_timeline,
    }


def execute_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 5: Execute approved recovery action on the simulator."""
    decision = state.get("governor_decision")
    proposal = state.get("proposed_action")
    timeline = state.get("timeline", [])

    if not decision or not proposal or not decision.approved:
        raise ValueError("Cannot execute unapproved recovery action")

    logger.info("Workflow [EXECUTE]: Applying action '%s'...", proposal.action_type)

    exec_result = execute_recovery_action(decision, proposal)

    updated_timeline = _append_timeline_event(
        timeline,
        stage="EXECUTE",
        summary=f"Executed: {exec_result.action_type}",
        details={"message": exec_result.message},
    )

    audit_timeline.record(
        stage=AuditStage.EXECUTED,
        action_type=exec_result.action_type,
        attempt_number=proposal.attempt_number,
        details={"message": exec_result.message},
        success=exec_result.executed,
    )

    return {
        "execution_result": exec_result,
        "status": "VERIFYING",
        "timeline": updated_timeline,
    }


def verify_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 6: Post-repair verification probe (health, DB, latency, test booking)."""
    proposal = state.get("proposed_action")
    attempt = state.get("attempt_count", 1)
    max_att = state.get("max_attempts", 3)
    timeline = state.get("timeline", [])

    logger.info("Workflow [VERIFY]: Running verification probe (attempt %d of %d)...", attempt, max_att)

    verif_result = verify_system_recovery()

    updated_timeline = _append_timeline_event(
        timeline,
        stage="VERIFY",
        summary=f"Verification {'PASSED' if verif_result.verified else 'FAILED'}",
        details={
            "verified": verif_result.verified,
            "health_ok": verif_result.health_ok,
            "database_ok": verif_result.database_ok,
            "latency_ok": verif_result.latency_ok,
            "booking_test_ok": verif_result.booking_test_ok,
            "details": verif_result.details,
        },
    )

    action_name = proposal.action_type if proposal else "unknown"
    audit_timeline.record(
        stage=AuditStage.VERIFIED,
        action_type=action_name,
        attempt_number=attempt,
        details={"verified": verif_result.verified, "details": verif_result.details},
        success=verif_result.verified,
    )

    if verif_result.verified:
        return {
            "verification_result": verif_result,
            "status": "SUCCESS",
            "timeline": updated_timeline,
        }
    else:
        new_attempt = attempt + 1
        new_status = "ESCALATED" if new_attempt > max_att else "RETRYING"
        return {
            "verification_result": verif_result,
            "attempt_count": new_attempt,
            "status": new_status,
            "timeline": updated_timeline,
        }


def escalate_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 7: Escalate to human operator when recovery cannot proceed safely."""
    decision = state.get("governor_decision")
    attempt = state.get("attempt_count", 1)
    timeline = state.get("timeline", [])

    reason = "Automated recovery halted."
    if decision and not decision.approved:
        reason = f"Safety Governor rejected action: {decision.reason}"
    elif attempt > state.get("max_attempts", 3):
        reason = f"Exceeded maximum recovery attempts ({state.get('max_attempts', 3)})."

    logger.warning("Workflow [ESCALATE]: %s", reason)

    updated_timeline = _append_timeline_event(
        timeline,
        stage="ESCALATE",
        summary=f"Incident Escalated: {reason}",
        details={"reason": reason, "attempt_count": attempt},
    )

    audit_timeline.record(
        stage=AuditStage.ESCALATED,
        action_type="escalation",
        attempt_number=attempt,
        details={"reason": reason},
        success=False,
    )

    return {
        "status": "ESCALATED",
        "error_message": reason,
        "timeline": updated_timeline,
    }

