"""
LangGraph node implementations for CivicShield incident response.

Each node represents a distinct phase of the multi-agent collaboration lifecycle:
- intake: Records trigger and initializes workflow state (Intake Controller).
- diagnose: Probes simulated clinic and collects structured evidence (Telemetry Collector).
- analyze: Diagnostic Analyst interprets raw telemetry and forms root cause hypothesis.
- plan: Recovery Planner selects allowlisted recovery action or diagnostic tool.
- safety_gate: Deterministic Safety Governor validates proposals against strict rules.
- shadow: Observes and evaluates proposed actions without executing repairs.
- await_approval: Pauses execution in Supervised Mode until human operator decision.
- execute: Applies safe recovery actions against simulator (Simulator Executor).
- verify: Runs post-repair verification checks to prove recovery (Verification Probe).
- escalate: Halts automation and requests human operator intervention.
"""

from datetime import datetime, timezone
import logging
import time
from typing import Any
import uuid

from app.agent.analyst import diagnostic_analyst
from app.agent.models import PlannerDecisionType
from app.agent.planner import investigation_planner
from app.diagnostics.tools import run_all_diagnostics
from app.recovery.executor import execute_recovery_action
from app.recovery.governor import validate_recovery_proposal
from app.recovery.models import ActionProposal, AuditStage
from app.recovery.timeline import audit_timeline
from app.recovery.verifier import verify_system_recovery

from .state import CivicShieldState, ExecutionEvent

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


def _record_execution_event(
    events: list[ExecutionEvent],
    run_id: str,
    node: str,
    agent_id: str,
    agent_type: str,
    event_type: str,
    status: str,
    input_summary: str,
    output_summary: str,
    structured_payload: dict[str, Any],
    handoff_to: str | None = None,
    duration_ms: float | None = None,
    error_detail: str | None = None,
) -> list[ExecutionEvent]:
    """Helper to append a structured ExecutionEvent to the telemetry stream."""
    new_events = list(events)
    seq = len(new_events) + 1
    event = ExecutionEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        run_id=run_id,
        seq=seq,
        timestamp=datetime.now(timezone.utc).isoformat(),
        node=node,
        agent_id=agent_id,
        agent_type=agent_type,
        event_type=event_type,
        status=status,
        input_summary=input_summary,
        output_summary=output_summary,
        structured_payload=structured_payload,
        handoff_to=handoff_to,
        duration_ms=duration_ms,
        error_detail=error_detail,
    )
    new_events.append(event)
    return new_events


def intake_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 1: Intake incident report and initialize workflow state."""
    t0 = time.perf_counter()
    desc = state.get("incident_description", "Automated incident intake")
    attempt = state.get("attempt_count", 1)
    max_att = state.get("max_attempts", 3)
    timeline = state.get("timeline", [])
    events = state.get("events", [])
    autonomy_mode = state.get("autonomy_mode", "autonomous")
    run_id = state.get("run_id") or f"run_{uuid.uuid4().hex[:8]}"

    logger.info("Workflow [INTAKE]: %s (mode=%s, run_id=%s)", desc, autonomy_mode, run_id)

    updated_timeline = _append_timeline_event(
        timeline,
        stage="INTAKE",
        summary=f"Incident ingested ({autonomy_mode.upper()} mode): {desc}",
        details={"attempt": attempt, "max_attempts": max_att, "autonomy_mode": autonomy_mode, "run_id": run_id},
    )

    audit_timeline.record(
        stage=AuditStage.PROPOSED,
        action_type="incident_intake",
        attempt_number=attempt,
        details={"incident": desc, "autonomy_mode": autonomy_mode},
        success=True,
    )

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    updated_events = _record_execution_event(
        events=events,
        run_id=run_id,
        node="intake",
        agent_id="intake_controller",
        agent_type="workflow_controller",
        event_type="node_complete",
        status="success",
        input_summary=f"Trigger payload: '{desc}' [Mode: {autonomy_mode.upper()}]",
        output_summary=f"Incident state initialized. Handoff to telemetry_collector (attempt {attempt}/{max_att})",
        structured_payload={
            "run_id": run_id,
            "incident_description": desc,
            "autonomy_mode": autonomy_mode,
            "attempt_count": attempt,
            "max_attempts": max_att,
        },
        handoff_to="telemetry_collector",
        duration_ms=duration_ms,
    )

    return {
        "run_id": run_id,
        "status": "DIAGNOSING",
        "autonomy_mode": autonomy_mode,
        "attempt_count": attempt,
        "max_attempts": max_att,
        "timeline": updated_timeline,
        "events": updated_events,
    }


def diagnose_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 2: Execute diagnostic suite and refresh structured evidence."""
    t0 = time.perf_counter()
    logger.info("Workflow [DIAGNOSE]: Probing clinic health, DB, config, latency...")

    report = run_all_diagnostics()
    timeline = state.get("timeline", [])
    events = state.get("events", [])
    run_id = state.get("run_id", "run_unknown")

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

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    updated_events = _record_execution_event(
        events=events,
        run_id=run_id,
        node="diagnose",
        agent_id="telemetry_collector",
        agent_type="deterministic_tool",
        event_type="tool_call",
        status="success",
        input_summary="Probing clinic infrastructure (health, PostgreSQL socket, configuration registry, latency SLA)",
        output_summary=summary,
        structured_payload=report.model_dump(),
        handoff_to="diagnostic_analyst",
        duration_ms=duration_ms,
    )

    return {
        "evidence": report,
        "status": "ANALYZING",
        "timeline": updated_timeline,
        "events": updated_events,
    }


def analyze_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 3: Diagnostic Analyst agent synthesizes raw telemetry into root-cause findings."""
    t0 = time.perf_counter()
    report = state.get("evidence")
    force_fallback = state.get("force_fallback", False)
    timeline = state.get("timeline", [])
    events = state.get("events", [])
    run_id = state.get("run_id", "run_unknown")

    logger.info("Workflow [ANALYZE]: Diagnostic Analyst evaluating evidence (force_fallback=%s)...", force_fallback)

    analysis = diagnostic_analyst.analyze(report=report, force_fallback=force_fallback)

    summary = (
        f"Analyst [{analysis.source}]: {analysis.suspected_component} -> {analysis.failure_mode} "
        f"({analysis.severity}, Confidence: {analysis.confidence_score * 100:.0f}%)"
    )

    updated_timeline = _append_timeline_event(
        timeline,
        stage="ANALYZE",
        summary=summary,
        details={
            "suspected_component": analysis.suspected_component,
            "failure_mode": analysis.failure_mode,
            "severity": analysis.severity,
            "hypothesis": analysis.hypothesis,
            "confidence_score": analysis.confidence_score,
            "recommend_recovery": analysis.recommend_recovery,
            "source": analysis.source,
        },
    )

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    updated_events = _record_execution_event(
        events=events,
        run_id=run_id,
        node="analyze",
        agent_id="diagnostic_analyst",
        agent_type="ai_agent",
        event_type="agent_handoff",
        status="success",
        input_summary=f"Raw diagnostic telemetry from telemetry_collector (Report ID: {report.generated_at.isoformat() if report else 'N/A'})",
        output_summary=f"Diagnosis: Component '{analysis.suspected_component}', Mode '{analysis.failure_mode}'. Handoff to recovery_planner.",
        structured_payload=analysis.model_dump(),
        handoff_to="recovery_planner",
        duration_ms=duration_ms,
    )

    return {
        "diagnostic_analysis": analysis,
        "hypothesis": analysis.hypothesis,
        "status": "PLANNING",
        "timeline": updated_timeline,
        "events": updated_events,
    }


def plan_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 4: Recovery Planner agent uses diagnostic findings to select safe recovery action."""
    t0 = time.perf_counter()
    report = state.get("evidence")
    analysis = state.get("diagnostic_analysis")
    force_fallback = state.get("force_fallback", False)
    attempt = state.get("attempt_count", 1)
    timeline = state.get("timeline", [])
    events = state.get("events", [])
    run_id = state.get("run_id", "run_unknown")

    logger.info("Workflow [PLAN]: Recovery Planner formulating plan (force_fallback=%s, attempt=%d)...", force_fallback, attempt)

    recommendation = investigation_planner.plan(report=report, analysis=analysis, force_fallback=force_fallback)

    proposed_action = None
    if recommendation.decision_type == PlannerDecisionType.RECOVER and recommendation.recovery_action:
        proposed_action = ActionProposal(
            action_type=recommendation.recovery_action,
            parameters=recommendation.parameters,
            rationale=recommendation.rationale,
            supporting_evidence=recommendation.supporting_evidence,
            attempt_number=attempt,
        )

    action_label = recommendation.recovery_action or (recommendation.diagnostic_tool.value if recommendation.diagnostic_tool else "NONE")
    summary = f"Plan [{recommendation.source}]: {recommendation.decision_type.value} -> {action_label}"

    updated_timeline = _append_timeline_event(
        timeline,
        stage="PLAN",
        summary=summary,
        details={
            "hypothesis": recommendation.hypothesis,
            "decision_type": recommendation.decision_type.value,
            "action": recommendation.recovery_action,
            "tool": recommendation.diagnostic_tool.value if recommendation.diagnostic_tool else None,
            "confidence": recommendation.confidence_score,
            "source": recommendation.source,
        },
    )

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    next_handoff = "safety_governor" if proposed_action else ("telemetry_collector" if recommendation.decision_type == PlannerDecisionType.INVESTIGATE else "escalation_controller")

    updated_events = _record_execution_event(
        events=events,
        run_id=run_id,
        node="plan",
        agent_id="recovery_planner",
        agent_type="ai_agent",
        event_type="agent_handoff",
        status="success",
        input_summary=f"Diagnostic findings from diagnostic_analyst: {analysis.suspected_component if analysis else 'UNKNOWN'} ({analysis.failure_mode if analysis else 'UNKNOWN'})",
        output_summary=f"Decision: {recommendation.decision_type.value} -> Proposed Action: '{action_label}'. Handoff to {next_handoff}.",
        structured_payload=recommendation.model_dump(),
        handoff_to=next_handoff,
        duration_ms=duration_ms,
    )

    return {
        "hypothesis": recommendation.hypothesis,
        "planner_recommendation": recommendation,
        "proposed_action": proposed_action,
        "status": "PLANNING_COMPLETED",
        "timeline": updated_timeline,
        "events": updated_events,
    }


def safety_gate_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 5: Deterministic Safety Governor validation."""
    t0 = time.perf_counter()
    proposal = state.get("proposed_action")
    timeline = state.get("timeline", [])
    events = state.get("events", [])
    run_id = state.get("run_id", "run_unknown")
    autonomy_mode = state.get("autonomy_mode", "autonomous")

    if not proposal:
        logger.warning("Workflow [SAFETY_GATE]: No proposed action in state to evaluate.")
        duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        updated_events = _record_execution_event(
            events=events,
            run_id=run_id,
            node="safety_gate",
            agent_id="safety_governor",
            agent_type="deterministic_guardrail",
            event_type="safety_evaluation",
            status="blocked",
            input_summary="No proposed action found in state",
            output_summary="Safety evaluation halted; escalating",
            structured_payload={"error": "missing_proposed_action"},
            handoff_to="escalation_controller",
            duration_ms=duration_ms,
            error_detail="Missing proposed action in state",
        )
        return {"status": "ESCALATED", "events": updated_events}

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

    # Determine handoff destination based on decision and autonomy mode
    if not decision.approved:
        next_target = "escalation_controller"
    elif autonomy_mode == "shadow":
        next_target = "shadow_evaluator"
    elif autonomy_mode == "supervised":
        next_target = "human_gate_controller"
    else:
        next_target = "simulator_executor"

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    updated_events = _record_execution_event(
        events=events,
        run_id=run_id,
        node="safety_gate",
        agent_id="safety_governor",
        agent_type="deterministic_guardrail",
        event_type="safety_evaluation",
        status="success" if decision.approved else "blocked",
        input_summary=f"Evaluating action '{proposal.action_type}' (Attempt {proposal.attempt_number}) with parameters {proposal.parameters}",
        output_summary=f"Governor verdict: {'APPROVED' if decision.approved else 'BLOCKED'}. {decision.reason}. Handoff to {next_target}.",
        structured_payload=decision.model_dump(),
        handoff_to=next_target,
        duration_ms=duration_ms,
        error_detail=decision.reason if not decision.approved else None,
    )

    return {
        "governor_decision": decision,
        "status": "APPROVED" if decision.approved else "REJECTED",
        "timeline": updated_timeline,
        "events": updated_events,
    }


def shadow_node(state: CivicShieldState) -> dict[str, Any]:
    """
    Node: Shadow Mode Evaluation.
    Evaluates proposed action against expected ground truth without executing repairs.
    Guarantees simulator is never modified in Shadow Mode.
    """
    t0 = time.perf_counter()
    from app.simulator.faults import fault_manager
    from app.simulator.models import FaultType

    proposal = state.get("proposed_action")
    decision = state.get("governor_decision")
    timeline = state.get("timeline", [])
    events = state.get("events", [])
    run_id = state.get("run_id", "run_unknown")

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

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    updated_events = _record_execution_event(
        events=events,
        run_id=run_id,
        node="shadow",
        agent_id="shadow_evaluator",
        agent_type="workflow_controller",
        event_type="node_complete",
        status="success",
        input_summary=f"Evaluating proposed repair '{proposed_type}' in non-intrusive Shadow Mode against ground truth '{expected_action}'",
        output_summary=f"Evaluation complete. Matches ground truth: {matches_expected}. Execution strictly prevented.",
        structured_payload={
            "proposed_action": proposed_type,
            "expected_action": expected_action,
            "matches_expected": matches_expected,
            "execution_bypassed": True,
        },
        handoff_to=None,
        duration_ms=duration_ms,
    )

    return {
        "status": "SHADOW_EVALUATED",
        "shadow_matches_expected": matches_expected,
        "shadow_expected_action": expected_action,
        "awaiting_approval": False,
        "timeline": updated_timeline,
        "events": updated_events,
    }


def await_approval_node(state: CivicShieldState) -> dict[str, Any]:
    """
    Node: Supervised Mode Gate.
    Pauses workflow execution pending explicit human operator decision.
    """
    t0 = time.perf_counter()
    proposal = state.get("proposed_action")
    decision = state.get("governor_decision")
    timeline = state.get("timeline", [])
    events = state.get("events", [])
    run_id = state.get("run_id", "run_unknown")

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

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    updated_events = _record_execution_event(
        events=events,
        run_id=run_id,
        node="await_approval",
        agent_id="human_gate_controller",
        agent_type="workflow_controller",
        event_type="human_review",
        status="paused",
        input_summary=f"Governor approved '{action_name}'. Pausing automation to await human operator sign-off.",
        output_summary="Workflow state paused. Pending operator approve/reject signal.",
        structured_payload={
            "proposed_action": action_name,
            "governor_decision": decision.model_dump() if decision else None,
            "awaiting_human_approval": True,
        },
        handoff_to="human_operator",
        duration_ms=duration_ms,
    )

    return {
        "status": "AWAITING_APPROVAL",
        "awaiting_approval": True,
        "timeline": updated_timeline,
        "events": updated_events,
    }


def execute_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 6: Execute approved recovery action on the simulator."""
    t0 = time.perf_counter()
    decision = state.get("governor_decision")
    proposal = state.get("proposed_action")
    timeline = state.get("timeline", [])
    events = state.get("events", [])
    run_id = state.get("run_id", "run_unknown")

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

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    updated_events = _record_execution_event(
        events=events,
        run_id=run_id,
        node="execute",
        agent_id="simulator_executor",
        agent_type="deterministic_tool",
        event_type="tool_call",
        status="success" if exec_result.executed else "failed",
        input_summary=f"Approved ActionProposal '{proposal.action_type}' (Attempt {proposal.attempt_number})",
        output_summary=f"Execution completed: {exec_result.message}. Handoff to verification_probe.",
        structured_payload=exec_result.model_dump(),
        handoff_to="verification_probe",
        duration_ms=duration_ms,
    )

    return {
        "execution_result": exec_result,
        "status": "VERIFYING",
        "timeline": updated_timeline,
        "events": updated_events,
    }


def verify_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 7: Post-repair verification probe (health, DB, latency, test booking)."""
    t0 = time.perf_counter()
    proposal = state.get("proposed_action")
    attempt = state.get("attempt_count", 1)
    max_att = state.get("max_attempts", 3)
    timeline = state.get("timeline", [])
    events = state.get("events", [])
    run_id = state.get("run_id", "run_unknown")

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

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    next_handoff = None if verif_result.verified else ("telemetry_collector" if attempt + 1 <= max_att else "escalation_controller")

    updated_events = _record_execution_event(
        events=events,
        run_id=run_id,
        node="verify",
        agent_id="verification_probe",
        agent_type="deterministic_tool",
        event_type="tool_call",
        status="success" if verif_result.verified else "failed",
        input_summary="Verification suite: endpoint health, database ping, latency benchmark, test appointment transaction",
        output_summary=f"Verification {'PASSED: Clinic fully healthy' if verif_result.verified else 'FAILED: Residual impairment detected'}",
        structured_payload=verif_result.model_dump(),
        handoff_to=next_handoff,
        duration_ms=duration_ms,
    )

    if verif_result.verified:
        return {
            "verification_result": verif_result,
            "status": "SUCCESS",
            "timeline": updated_timeline,
            "events": updated_events,
        }
    else:
        new_attempt = attempt + 1
        new_status = "ESCALATED" if new_attempt > max_att else "RETRYING"
        return {
            "verification_result": verif_result,
            "attempt_count": new_attempt,
            "status": new_status,
            "timeline": updated_timeline,
            "events": updated_events,
        }


def escalate_node(state: CivicShieldState) -> dict[str, Any]:
    """Node 8: Escalate to human operator when recovery cannot proceed safely."""
    t0 = time.perf_counter()
    decision = state.get("governor_decision")
    attempt = state.get("attempt_count", 1)
    timeline = state.get("timeline", [])
    events = state.get("events", [])
    run_id = state.get("run_id", "run_unknown")
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

    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    updated_events = _record_execution_event(
        events=events,
        run_id=run_id,
        node="escalate",
        agent_id="escalation_controller",
        agent_type="workflow_controller",
        event_type="workflow_escalate",
        status="escalated",
        input_summary=f"Escalation condition met (Attempt {attempt}): {reason}",
        output_summary=f"Automation halted safely. Alert dispatched to human on-call operator.",
        structured_payload={"reason": reason, "attempt_count": attempt},
        handoff_to="human_operator",
        duration_ms=duration_ms,
        error_detail=reason,
    )

    return {
        "status": "ESCALATED",
        "error_message": reason,
        "timeline": updated_timeline,
        "events": updated_events,
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
    t0 = time.perf_counter()
    timeline = list(paused_state.get("timeline", []))
    events = list(paused_state.get("events", []))
    proposal_dict = paused_state.get("proposed_action")
    run_id = paused_state.get("run_id", "run_unknown")
    action_type = "unknown"
    if isinstance(proposal_dict, dict):
        action_type = proposal_dict.get("action_type", "unknown")
    elif proposal_dict and hasattr(proposal_dict, "action_type"):
        action_type = proposal_dict.action_type

    attempt = paused_state.get("attempt_count", 1)

    # Record human decision event
    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    events = _record_execution_event(
        events=events,
        run_id=run_id,
        node="human_decision",
        agent_id="human_operator",
        agent_type="human_operator",
        event_type="human_review",
        status="success" if approved else "blocked",
        input_summary=f"Operator presented with proposed action '{action_type}'",
        output_summary=f"Human operator {'APPROVED' if approved else 'REJECTED'} action '{action_type}'. {'Reason: ' + rejection_reason if rejection_reason else ''}",
        structured_payload={"approved": approved, "rejection_reason": rejection_reason, "action_type": action_type},
        handoff_to="simulator_executor" if approved else "escalation_controller",
        duration_ms=duration_ms,
        error_detail=rejection_reason if not approved else None,
    )

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
        escalate_state["events"] = events
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
    resume_state["events"] = events

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
