"""
Integration and Unit Tests for Multi-Agent Collaboration Trace & Event Telemetry.

Validates:
1. Diagnostic Analyst agent output schema and deterministic diagnostic rules.
2. Recovery Planner consumption of DiagnosticAnalysis findings.
3. Chronological ExecutionEvent telemetry recording across all workflow phases.
4. Agent handoff chain (Intake -> Telemetry -> Analyst -> Planner -> Governor -> Executor -> Verifier).
5. Autonomy Mode trace behavior (Autonomous, Supervised Human Decision, Shadow Evaluation).
6. Governor rejection event capture when an unsafe action is proposed.
"""

from fastapi.testclient import TestClient
import pytest

from app.agent.analyst import diagnostic_analyst
from app.agent.models import DiagnosticAnalysis, PlannerDecisionType
from app.agent.planner import investigation_planner
from app.main import app
from app.simulator.faults import fault_manager
from app.simulator.models import FaultType
from app.workflow.graph import civicshield_workflow
from app.workflow.state import AutonomyMode, CivicShieldState

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_simulator_state():
    """Ensure a clean simulator slate before and after every test."""
    fault_manager.reset()
    yield
    fault_manager.reset()


# ---------------------------------------------------------------------------
# 1. Diagnostic Analyst Agent Unit Tests
# ---------------------------------------------------------------------------

def test_diagnostic_analyst_healthy_baseline():
    """Analyst correctly classifies a healthy system as low severity with recommend_recovery=False."""
    analysis = diagnostic_analyst.analyze(force_fallback=True)
    assert isinstance(analysis, DiagnosticAnalysis)
    assert analysis.suspected_component == "healthy"
    assert analysis.failure_mode == "healthy"
    assert analysis.severity == "LOW"
    assert analysis.confidence_score == 1.0
    assert not analysis.recommend_recovery
    assert "healthy_baseline" in analysis.evidence_summary


def test_diagnostic_analyst_identifies_invalid_db_config():
    """Analyst detects configuration drift and maps to invalid_host_config failure mode."""
    fault_manager.inject(FaultType.INVALID_DB_CONFIG)
    analysis = diagnostic_analyst.analyze(force_fallback=True)

    assert analysis.suspected_component == "configuration"
    assert analysis.failure_mode == "invalid_host_config"
    assert analysis.severity == "HIGH"
    assert analysis.recommend_recovery is True
    assert analysis.confidence_score >= 0.90
    assert "config_divergence" in analysis.evidence_summary


def test_diagnostic_analyst_identifies_db_unavailable():
    """Analyst detects database socket refusal and flags critical severity."""
    fault_manager.inject(FaultType.DB_UNAVAILABLE)
    analysis = diagnostic_analyst.analyze(force_fallback=True)

    assert analysis.suspected_component == "database"
    assert analysis.failure_mode == "db_connection_refused"
    assert analysis.severity == "CRITICAL"
    assert analysis.recommend_recovery is True
    assert "connection_refused" in analysis.evidence_summary


def test_diagnostic_analyst_identifies_high_latency():
    """Analyst detects SLA breach and flags latency violation."""
    fault_manager.inject(FaultType.HIGH_LATENCY)
    analysis = diagnostic_analyst.analyze(force_fallback=True)

    assert analysis.suspected_component == "network"
    assert analysis.failure_mode == "latency_sla_violation"
    assert analysis.severity == "MEDIUM"
    assert analysis.recommend_recovery is True
    assert "high_latency" in analysis.evidence_summary


def test_diagnostic_analyst_identifies_adversarial_injection():
    """Analyst detects rogue/unsafe proposal fault and flags critical security anomaly."""
    fault_manager.inject(FaultType.UNSAFE_PROPOSAL_SIM)
    analysis = diagnostic_analyst.analyze(force_fallback=True)

    assert analysis.suspected_component == "database_security"
    assert analysis.failure_mode == "adversarial_injection"
    assert analysis.severity == "CRITICAL"
    assert "simulated_adversarial_event" in analysis.evidence_summary


# ---------------------------------------------------------------------------
# 2. Multi-Agent Handoff: Analyst -> Planner
# ---------------------------------------------------------------------------

def test_planner_consumes_analyst_findings():
    """Planner receives Analyst's DiagnosticAnalysis and formulates allowlisted recovery."""
    fault_manager.inject(FaultType.INVALID_DB_CONFIG)
    analysis = diagnostic_analyst.analyze(force_fallback=True)
    plan = investigation_planner.plan(analysis=analysis, force_fallback=True)

    assert plan.decision_type == PlannerDecisionType.RECOVER
    assert plan.recovery_action == "restore_baseline_config"
    assert plan.confidence_score >= 0.90
    assert "invalid_host_config" in plan.rationale or "config" in plan.rationale.lower()


# ---------------------------------------------------------------------------
# 3. ExecutionEvent Telemetry & Collaboration Trace
# ---------------------------------------------------------------------------

def test_collaboration_trace_autonomous_recovery():
    """
    End-to-end Autonomous run emits complete sequence of ExecutionEvents
    with correct agent IDs, agent types, handoffs, and measured durations.
    """
    fault_manager.inject(FaultType.INVALID_DB_CONFIG)

    res = client.post(
        "/workflow/run",
        json={
            "incident_description": "Config fault recovery trace test",
            "autonomy_mode": "autonomous",
            "force_fallback": True,
        },
    )
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCCESS"
    assert data["diagnostic_analysis"] is not None
    assert data["diagnostic_analysis"]["suspected_component"] == "configuration"

    events = data["events"]
    assert len(events) >= 7

    # Verify monotonic sequencing and run ID consistency
    run_id = events[0]["run_id"]
    for i, evt in enumerate(events):
        assert evt["seq"] == i + 1
        assert evt["run_id"] == run_id
        assert evt["duration_ms"] is not None and evt["duration_ms"] >= 0.0

    # Verify agent roles in order
    nodes = [e["node"] for e in events]
    agent_ids = [e["agent_id"] for e in events]
    agent_types = [e["agent_type"] for e in events]

    assert nodes == ["intake", "diagnose", "analyze", "plan", "safety_gate", "execute", "verify"]
    assert agent_ids == [
        "intake_controller",
        "telemetry_collector",
        "diagnostic_analyst",
        "recovery_planner",
        "safety_governor",
        "simulator_executor",
        "verification_probe",
    ]
    assert agent_types == [
        "workflow_controller",
        "deterministic_tool",
        "ai_agent",
        "ai_agent",
        "deterministic_guardrail",
        "deterministic_tool",
        "deterministic_tool",
    ]

    # Verify handoffs
    assert events[0]["handoff_to"] == "telemetry_collector"
    assert events[1]["handoff_to"] == "diagnostic_analyst"
    assert events[2]["handoff_to"] == "recovery_planner"
    assert events[3]["handoff_to"] == "safety_governor"
    assert events[4]["handoff_to"] == "simulator_executor"
    assert events[5]["handoff_to"] == "verification_probe"
    assert events[6]["handoff_to"] is None


def test_collaboration_trace_safety_rejection():
    """
    Unsafe proposal simulation triggers Governor block, recording
    status='blocked' on safety_governor and handoff to escalation_controller.
    """
    fault_manager.inject(FaultType.UNSAFE_PROPOSAL_SIM)

    res = client.post(
        "/workflow/run",
        json={
            "incident_description": "Unsafe proposal injection trace test",
            "autonomy_mode": "autonomous",
            "force_fallback": True,
        },
    )
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "ESCALATED"
    events = data["events"]

    governor_event = next(e for e in events if e["node"] == "safety_gate")
    assert governor_event["agent_id"] == "safety_governor"
    assert governor_event["status"] == "blocked"
    assert governor_event["handoff_to"] == "escalation_controller"
    assert "forbidden" in governor_event["output_summary"].lower() or "blocked" in governor_event["output_summary"].lower()

    escalate_event = next(e for e in events if e["node"] == "escalate")
    assert escalate_event["agent_id"] == "escalation_controller"
    assert escalate_event["status"] == "escalated"
    assert escalate_event["handoff_to"] == "human_operator"


def test_collaboration_trace_shadow_mode():
    """Shadow mode records non-intrusive evaluation and bypasses execution."""
    fault_manager.inject(FaultType.DB_UNAVAILABLE)

    res = client.post(
        "/workflow/run",
        json={
            "incident_description": "Shadow mode evaluation trace test",
            "autonomy_mode": "shadow",
            "force_fallback": True,
        },
    )
    assert res.status_code == 200
    data = res.json()

    events = data["events"]
    assert any(e["node"] == "shadow" for e in events)
    shadow_event = next(e for e in events if e["node"] == "shadow")
    assert shadow_event["agent_id"] == "shadow_evaluator"
    assert shadow_event["agent_type"] == "workflow_controller"
    assert shadow_event["structured_payload"]["execution_bypassed"] is True

    # Ensure execute node was NEVER called
    assert not any(e["node"] == "execute" for e in events)


def test_collaboration_trace_supervised_mode_approval_and_rejection():
    """Supervised mode pauses with human_gate_controller event, then records human_operator event."""
    fault_manager.inject(FaultType.HIGH_LATENCY)

    # 1. Run supervised workflow -> pauses awaiting human
    res_pause = client.post(
        "/workflow/run",
        json={
            "incident_description": "Supervised approval trace test",
            "autonomy_mode": "supervised",
            "force_fallback": True,
        },
    )
    assert res_pause.status_code == 200
    pause_data = res_pause.json()
    assert pause_data["status"] == "AWAITING_APPROVAL"

    events = pause_data["events"]
    pause_event = events[-1]
    assert pause_event["node"] == "await_approval"
    assert pause_event["agent_id"] == "human_gate_controller"
    assert pause_event["status"] == "paused"
    assert pause_event["handoff_to"] == "human_operator"

    # 2. Operator approves
    res_resume = client.post(
        "/workflow/resume",
        json={
            "approved": True,
            "paused_state": pause_data,
        },
    )
    assert res_resume.status_code == 200
    resume_data = res_resume.json()
    assert resume_data["status"] == "SUCCESS"

    resume_events = resume_data["events"]
    human_event = next(e for e in resume_events if e["agent_id"] == "human_operator")
    assert human_event["agent_type"] == "human_operator"
    assert human_event["status"] == "success"
    assert human_event["handoff_to"] == "simulator_executor"
