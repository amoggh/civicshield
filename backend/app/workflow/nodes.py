"""
LangGraph node implementations for CivicShield incident response.

Each node represents a distinct phase of the investigation and recovery lifecycle:
- intake: Records the trigger and initial incident context.
- diagnose: Probes the simulated clinic and collects structured evidence.
- plan: Formulates a hypothesis and selects a recovery action or diagnostic.
- safety_gate: Validates proposed actions against deterministic Python rules.
- shadow: Observes and evaluates proposed actions without executing repairs.
- await_approval: Pauses execution in Supervised Mode until human operator decision.
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
    autonomy_mode = state.get("autonomy_mode", "autonomous")

    logger.info("Workflow [INTAKE]: %s (mode=%s)", desc, autonomy_mode)

    updated_timeline = _append_timeline_event(
        timeline,
        stage="INTAKE",
        summary=f"Incident ingested ({autonomy_mode.upper()} mode): {desc}",
        details={"attempt": attempt, "max_attempts": max_att, "autonomy_mode": autonomy_mode},
    )

    audit_timeline.record(
        stage=AuditStage.PROPOSED,
        action_type="incident_intake",
        attempt_number=attempt,
        details={"incident": desc, "autonomy_mode": autonomy_mode},
        success=True,
    )

    return {
        "status": "DIAGNOSING",
        "autonomy_mode": autonomy_mode,
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


def shadow_node(state: CivicShieldState) -> dict[str, Any]:
    """
    Node: Shadow Mode Evaluation.
    Evaluates proposed action against expected ground truth without executing repairs.
    Guarantees simulator is never modified in Shadow Mode.
    """
    from app.simulator.faults import fault_manager
    from app.simulator.models import FaultType

    proposal = state.get("proposed_action")
    decision = state.get("governor_decision")
    timeline = state.get("timeline", [])

    # Determine expected ground truth action from active simulator faults
    expected_action = None
    if fault_manager.is_active(FaultType.INVALID_DB_CONFIG):
        expected_action = "restore_baseline_config"
    elif fault_manager.is_active(FaultType.DB_UNAVAILABLE):
        expected_action = "reconnect_database"
    elif fault_manager.is_active(FaultType.HIGH_LATENCY):
        expected_action = "clear_latency_delay"
    elif fault_manager.is_active(FaultType.UNSAFE_PROPOSAL_SIM):
        expected_action = "escalate"

    proposed_type = proposal.action_type if proposal else None
    matches_expected = (proposed_type == expected_action) if (proposed_type and expected_action) else False

    governor_status = "WOULD_APPROVE" if (decision and decision.approved) else "WOULD_REJECT"
    summary = (
        f"Shadow Mode: Proposal '{proposed_type}' evaluated ({governor_status}). "
        f"Expected: '{expected_action}'. Matches ground truth: {matches_expected}. "
        f"Execution strictly bypassed."
    )

    updated_timeline = _append_timeline_event(
        timeline,
        stage="SHADOW_CHECK",
        summary=summary,
        details={
            "proposed_action": proposed_type,
            "governor_decision": decision.approved if decision else False,
            "expected_action": expected_action,
            "matches_expected": matches_expected,
            "execution_bypassed": True,
        },
    )

    audit_timeline.record(
        stage=AuditStage.SAFETY_CHECK,
        action_type=proposed_type or "none",
        attempt_number=state.get("attempt_count", 1),
        details={
            "mode": "shadow",
            "matches_expected": matches_expected,
            "executed": False,
        },
        success=matches_expected,
    )

    return {
        "status": "SHADOW_EVALUATED",
        "shadow_matches_expected": matches_expected,
        "shadow_expected_action": expected_action,
        "awaiting_approval": False,
        "timeline": updated_timeline,
    }


def await_approval_node(state: CivicShieldState) -> dict[str, Any]:
    """
    Node: Supervised Mode Gate.
    Pauses workflow execution pending explicit human operator decision.
    """
    proposal = state.get("proposed_action")
    decision = state.get("governor_decision")
    timeline = state.get("timeline", [])

    action_name = proposal.action_type if proposal else "unknown"
    summary = f"Supervised Mode: Proposal '{action_name}' approved by Safety Governor. Paused awaiting human approval."

    updated_timeline = _append_timeline_event(
        timeline,
        stage="SUPERVISED_GATE",
        summary=summary,
        details={
            "proposed_action": action_name,
            "governor_approved": decision.approved if decision else False,
            "governor_reason": decision.reason if decision else "No decision",
            "awaiting_human_approval": True,
        },
    )

    return {
        "status": "AWAITING_APPROVAL",
        "awaiting_approval": True,
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
    custom_error = state.get("error_message")

    reason = custom_error or "Automated recovery halted."
    if not custom_error:
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


def resume_supervised_workflow(
    paused_state: dict[str, Any],
    approved: bool,
    rejection_reason: str | None = None,
) -> dict[str, Any]:
    """
    Resume a paused workflow in Supervised Mode following human operator decision.
    If approved=True:
        Logs human authorization and executes approved action -> verify.
    If approved=False:
        Logs human rejection, escalates to human on-call, and strictly skips execution.
    """
    timeline = list(paused_state.get("timeline", []))
    proposal_dict = paused_state.get("proposed_action")
    action_type = "unknown"
    if isinstance(proposal_dict, dict):
        action_type = proposal_dict.get("action_type", "unknown")
    elif proposal_dict and hasattr(proposal_dict, "action_type"):
        action_type = proposal_dict.action_type

    attempt = paused_state.get("attempt_count", 1)

    if not approved:
        reason = rejection_reason or "Operator denied repair authorization."
        logger.warning("Workflow [SUPERVISED]: Human operator REJECTED action '%s': %s", action_type, reason)

        updated_timeline = _append_timeline_event(
            timeline,
            stage="SUPERVISED_REJECTION",
            summary=f"Human Operator REJECTED '{action_type}': {reason}",
            details={"action_type": action_type, "reason": reason, "executed": False},
        )

        audit_timeline.record(
            stage=AuditStage.ESCALATED,
            action_type=action_type,
            attempt_number=attempt,
            details={"reason": reason, "supervised_rejection": True},
            success=False,
        )

        escalate_state = dict(paused_state)
        escalate_state["status"] = "ESCALATED"
        escalate_state["human_approved"] = False
        escalate_state["rejection_reason"] = reason
        escalate_state["awaiting_approval"] = False
        escalate_state["timeline"] = updated_timeline
        escalate_state["error_message"] = f"Supervised action rejected by operator: {reason}"
        return escalate_state

    # Human approved the action
    logger.info("Workflow [SUPERVISED]: Human operator APPROVED action '%s'. Executing...", action_type)

    updated_timeline = _append_timeline_event(
        timeline,
        stage="SUPERVISED_APPROVAL",
        summary=f"Human Operator APPROVED action '{action_type}'. Proceeding to verified execution.",
        details={"action_type": action_type, "human_approved": True},
    )

    resume_state = dict(paused_state)
    resume_state["human_approved"] = True
    resume_state["awaiting_approval"] = False
    resume_state["timeline"] = updated_timeline

    # Convert proposal dict back to ActionProposal if needed
    if isinstance(resume_state.get("proposed_action"), dict):
        resume_state["proposed_action"] = ActionProposal(**resume_state["proposed_action"])
    elif not resume_state.get("proposed_action") and resume_state.get("planner_recommendation"):
        rec = resume_state["planner_recommendation"]
        act = rec.get("recovery_action") if isinstance(rec, dict) else getattr(rec, "recovery_action", None)
        params = rec.get("parameters", {}) if isinstance(rec, dict) else getattr(rec, "parameters", {})
        rat = rec.get("rationale", "") if isinstance(rec, dict) else getattr(rec, "rationale", "")
        evi = rec.get("supporting_evidence", []) if isinstance(rec, dict) else getattr(rec, "supporting_evidence", [])
        if act:
            resume_state["proposed_action"] = ActionProposal(
                action_type=act,
                parameters=params,
                rationale=rat,
                supporting_evidence=evi,
                attempt_number=resume_state.get("attempt_count", 1),
            )

    from app.recovery.models import GovernorDecision
    if isinstance(resume_state.get("governor_decision"), dict):
        resume_state["governor_decision"] = GovernorDecision(**resume_state["governor_decision"])

    # 1. Execute recovery action
    exec_update = execute_node(resume_state)
    resume_state.update(exec_update)

    # 2. Run verification probe
    verif_update = verify_node(resume_state)
    resume_state.update(verif_update)

    return resume_state
