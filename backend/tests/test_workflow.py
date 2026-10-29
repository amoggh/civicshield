"""
Tests for Phase 6 — LangGraph Stateful Incident Response Workflow.

Verifies:
  - Full end-to-end recovery path (Intake -> Diagnose -> Plan -> Safety Gate -> Execute -> Verify -> Success).
  - Unsafe action rejection path routing directly to Escalation (Execution is never touched).
  - Bounded retry loop: Verification failure retries up to 3 times, then escalates.
  - Healthy baseline terminates cleanly at Plan without unnecessary actions.
  - REST endpoints /workflow/run and /workflow/mermaid execute smoothly.
  - Zero live LLM or external network dependencies.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.agent.models import PlannerDecisionType, PlannerRecommendation
from app.main import app
from app.recovery.models import ActionProposal, RecoveryActionType
from app.recovery.timeline import audit_timeline
from app.simulator.faults import fault_manager
from app.simulator.models import FaultType
from app.workflow.graph import civicshield_workflow
from app.workflow.state import CivicShieldState


@pytest.fixture(autouse=True)
def clean_state():
    """Reset simulator and audit timeline before and after every test."""
    fault_manager.reset()
    audit_timeline.clear()
    yield
    fault_manager.reset()
    audit_timeline.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Full Successful Recovery Path
# ---------------------------------------------------------------------------


def test_workflow_full_recovery_success():
    """
    Simulate full incident recovery through LangGraph:
    1. Fault: invalid database config.
    2. Workflow runs through intake -> diagnose -> plan -> safety -> execute -> verify.
    3. Final state is SUCCESS, verification verified, timeline complete.
    """
    fault_manager.inject(
        FaultType.INVALID_DB_CONFIG,
        {"corrupt_host": "unreachable-db.internal", "corrupt_port": 9999},
    )

    initial_state: CivicShieldState = {
        "incident_description": "Clinic appointments failing due to DB host resolution errors.",
        "force_fallback": True,
        "attempt_count": 1,
        "max_attempts": 3,
        "timeline": [],
    }

    final_state = civicshield_workflow.invoke(initial_state)

    # Assert final status and recovery validation
    assert final_state["status"] == "SUCCESS"
    assert final_state["verification_result"] is not None
    assert final_state["verification_result"].verified is True
    assert final_state["execution_result"] is not None
    assert final_state["execution_result"].executed is True
    assert final_state["governor_decision"].approved is True

    # Assert timeline preserves full sequence of milestones
    timeline_stages = [e["stage"] for e in final_state["timeline"]]
    assert "INTAKE" in timeline_stages
    assert "DIAGNOSE" in timeline_stages
    assert "PLAN" in timeline_stages
    assert "SAFETY_CHECK" in timeline_stages
    assert "EXECUTE" in timeline_stages
    assert "VERIFY" in timeline_stages
    assert "ESCALATE" not in timeline_stages


# ---------------------------------------------------------------------------
# 2. Safety Governor Rejection -> Escalation Path
# ---------------------------------------------------------------------------


def test_workflow_unsafe_action_escalates_and_never_executes():
    """
    When an unsafe action (e.g. drop_database) is proposed:
    - Safety gate blocks it (approved=False).
    - Edge routes directly to escalate -> END.
    - Execute node is NEVER executed.
    """
    fault_manager.inject(FaultType.DB_UNAVAILABLE)

    # Mock planner to simulate an adversarial or hallucinated unsafe recommendation
    unsafe_rec = PlannerRecommendation(
        decision_type=PlannerDecisionType.RECOVER,
        recovery_action=RecoveryActionType.DROP_DATABASE.value,
        parameters={"cascade": True},
        hypothesis="Database corrupt; dropping database.",
        rationale="Wipe database.",
        supporting_evidence=["db_unavailable"],
        confidence_score=0.9,
    )

    with patch("app.workflow.nodes.investigation_planner.plan", return_value=unsafe_rec):
        initial_state: CivicShieldState = {
            "incident_description": "Simulated dangerous hallucination injection",
            "force_fallback": True,
            "attempt_count": 1,
            "max_attempts": 3,
            "timeline": [],
        }

        final_state = civicshield_workflow.invoke(initial_state)

        # Assert Escalation
        assert final_state["status"] == "ESCALATED"
        assert final_state["governor_decision"].approved is False
        assert final_state["governor_decision"].requires_human_escalation is True

        # Assert EXECUTE was bypassed entirely
        assert final_state.get("execution_result") is None
        timeline_stages = [e["stage"] for e in final_state["timeline"]]
        assert "SAFETY_CHECK" in timeline_stages
        assert "ESCALATE" in timeline_stages
        assert "EXECUTE" not in timeline_stages


# ---------------------------------------------------------------------------
# 3. Bounded Retry Exhaustion -> Escalation Path
# ---------------------------------------------------------------------------


def test_workflow_exhausts_retries_and_escalates():
    """
    When verification fails repeatedly:
    - Graph retries up to max_attempts (3).
    - Upon exceeding attempt 3, routes to escalate.
    """
    fault_manager.inject(FaultType.DB_UNAVAILABLE)

    # Mock execute_recovery_action to be a no-op so the fault is never actually resolved
    from app.recovery.models import ExecutionResult
    from datetime import datetime, timezone

    dummy_exec = ExecutionResult(
        executed=True,
        action_type="reconnect_database",
        message="Simulated failed reconnect attempt.",
        timestamp=datetime.now(timezone.utc),
    )

    with patch("app.workflow.nodes.execute_recovery_action", return_value=dummy_exec):
        initial_state: CivicShieldState = {
            "incident_description": "Unresolvable database severed connection",
            "force_fallback": True,
            "attempt_count": 1,
            "max_attempts": 3,
            "timeline": [],
        }

        final_state = civicshield_workflow.invoke(initial_state)

        # Assert Escalation after bounded retries
        assert final_state["status"] == "ESCALATED"
        assert final_state["attempt_count"] > 3
        timeline_stages = [e["stage"] for e in final_state["timeline"]]
        assert "ESCALATE" in timeline_stages


# ---------------------------------------------------------------------------
# 4. Healthy Baseline Path
# ---------------------------------------------------------------------------


def test_workflow_healthy_baseline_terminates_at_plan():
    """
    When the system is already healthy:
    - Planner returns NO_ACTION.
    - Graph routes directly from plan to END.
    """
    initial_state: CivicShieldState = {
        "incident_description": "Routine health verification check",
        "force_fallback": True,
        "attempt_count": 1,
        "max_attempts": 3,
        "timeline": [],
    }

    final_state = civicshield_workflow.invoke(initial_state)

    timeline_stages = [e["stage"] for e in final_state["timeline"]]
    assert "INTAKE" in timeline_stages
    assert "DIAGNOSE" in timeline_stages
    assert "PLAN" in timeline_stages
    assert "EXECUTE" not in timeline_stages
    assert "ESCALATE" not in timeline_stages


# ---------------------------------------------------------------------------
# 5. REST Endpoints
# ---------------------------------------------------------------------------


def test_workflow_api_run_endpoint(client):
    """POST /workflow/run executes and returns structured response."""
    fault_manager.inject(
        FaultType.INVALID_DB_CONFIG,
        {"corrupt_host": "bad-host.internal", "corrupt_port": 8888},
    )

    resp = client.post(
        "/workflow/run",
        json={
            "incident_description": "API-triggered incident recovery",
            "force_fallback": True,
            "max_attempts": 3,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "SUCCESS"
    assert data["verification_result"]["verified"] is True
    assert len(data["timeline"]) >= 5


def test_workflow_mermaid_endpoint(client):
    """GET /workflow/mermaid returns a valid mermaid definition."""
    resp = client.get("/workflow/mermaid")
    assert resp.status_code == 200
    assert "graph TD" in resp.json()["mermaid"] or "flowchart TD" in resp.json()["mermaid"] or "subgraph" in resp.json()["mermaid"] or "intake" in resp.json()["mermaid"]

