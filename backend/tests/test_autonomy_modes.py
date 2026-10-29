"""
Unit and Integration tests for CivicShield's Three Autonomy Modes and Safety Rejection Scenarios.

Verifies:
1. Shadow Mode:
   - Evaluates proposals against ground truth without executing repairs.
   - Leaves clinic simulator 100% unmodified.
2. Supervised Mode:
   - Pauses execution with AWAITING_APPROVAL upon Safety Governor validation.
   - Respects human rejection: logs justification, escalates, never modifies service.
   - Executes and verifies upon explicit human approval.
3. Autonomous Mode:
   - Automatically executes approved, allowlisted actions.
4. Deterministic Safety Rejections:
   - Destructive proposals (drop tables, rm commands) are always blocked.
   - Non-allowlisted actions are rejected.
   - Missing or insufficient evidence preconditions trigger rejection.
   - Repeated failures bound retries (<= 3) and escalate.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.recovery.governor import validate_recovery_proposal
from app.recovery.models import ActionProposal
from app.simulator.config import active_config
from app.simulator.faults import fault_manager
from app.simulator.models import FaultType
from app.workflow.router import run_incident_response_workflow
from app.workflow.state import AutonomyMode, WorkflowRunRequest


@pytest.fixture(autouse=True)
def clean_state():
    """Ensure simulator state is clean before and after each test."""
    fault_manager.reset()
    yield
    fault_manager.reset()


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Shadow Mode Tests
# ---------------------------------------------------------------------------


def test_shadow_mode_never_executes_repairs_and_matches_ground_truth(client):
    """
    Shadow Mode:
    - Analyzes diagnostics and passes proposal through Safety Governor.
    - Evaluates match with ground truth.
    - Strictly BYPASSES execution; simulated service remains degraded.
    """
    fault_manager.inject(
        FaultType.INVALID_DB_CONFIG,
        {"corrupt_host": "drifted-host.internal", "corrupt_port": 9999},
    )
    assert active_config.db_port == 9999

    resp = client.post(
        "/workflow/run",
        json={
            "incident_description": "Testing Shadow Mode on drifted config",
            "autonomy_mode": "shadow",
            "force_fallback": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    # Workflow marks shadow evaluated
    assert data["status"] == "SHADOW_EVALUATED"
    assert data["autonomy_mode"] == "shadow"
    assert data["execution_result"] is None
    assert data["verification_result"] is None
    assert data["awaiting_approval"] is False

    # Ground truth comparison: correctly identified restore_baseline_config
    assert data["shadow_matches_expected"] is True
    assert data["shadow_expected_action"] == "restore_baseline_config"
    assert data["governor_decision"]["approved"] is True

    # Crucial check: Simulator state is UNTOUCHED
    assert active_config.db_port == 9999

    # Timeline includes shadow check
    stages = [event["stage"] for event in data["timeline"]]
    assert "SHADOW_CHECK" in stages
    assert "EXECUTE" not in stages


# ---------------------------------------------------------------------------
# 2. Supervised Mode Tests
# ---------------------------------------------------------------------------


def test_supervised_mode_pauses_for_human_approval(client):
    """
    Supervised Mode (Pause):
    - When Safety Governor approves, workflow pauses in AWAITING_APPROVAL.
    - No execution takes place while awaiting decision.
    """
    fault_manager.inject(
        FaultType.INVALID_DB_CONFIG,
        {"corrupt_host": "drifted-host.internal", "corrupt_port": 9999},
    )

    resp = client.post(
        "/workflow/run",
        json={
            "incident_description": "Supervised mode approval test",
            "autonomy_mode": "supervised",
            "force_fallback": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "AWAITING_APPROVAL"
    assert data["awaiting_approval"] is True
    assert data["governor_decision"]["approved"] is True
    assert data["execution_result"] is None

    # Service remains broken pending approval
    assert active_config.db_port == 9999

    stages = [event["stage"] for event in data["timeline"]]
    assert "SUPERVISED_GATE" in stages
    assert "EXECUTE" not in stages


def test_supervised_mode_human_rejection_prevents_execution(client):
    """
    Supervised Mode (Rejection):
    - Operator rejects proposal.
    - System transitions to ESCALATED, records rejection justification, skips execution.
    """
    fault_manager.inject(
        FaultType.INVALID_DB_CONFIG,
        {"corrupt_host": "drifted-host.internal", "corrupt_port": 9999},
    )

    # 1. Run initial paused workflow
    initial_resp = client.post(
        "/workflow/run",
        json={
            "incident_description": "Supervised mode rejection test",
            "autonomy_mode": "supervised",
            "force_fallback": True,
        },
    )
    paused_state = initial_resp.json()
    assert paused_state["status"] == "AWAITING_APPROVAL"

    # 2. Submit human operator rejection
    resume_resp = client.post(
        "/workflow/resume",
        json={
            "approved": False,
            "rejection_reason": "Maintenance window closed; manual DBA review required.",
            "paused_state": paused_state,
        },
    )
    assert resume_resp.status_code == 200
    resumed_data = resume_resp.json()

    assert resumed_data["status"] == "ESCALATED"
    assert resumed_data["human_approved"] is False
    assert resumed_data["execution_result"] is None

    # Verify simulator was strictly NOT modified
    assert active_config.db_port == 9999

    stages = [event["stage"] for event in resumed_data["timeline"]]
    assert "SUPERVISED_REJECTION" in stages
    assert "EXECUTE" not in stages


def test_supervised_mode_human_approval_executes_and_verifies(client):
    """
    Supervised Mode (Approval):
    - Operator approves proposal.
    - Workflow proceeds to execute recovery action and runs verification probe.
    """
    fault_manager.inject(
        FaultType.INVALID_DB_CONFIG,
        {"corrupt_host": "drifted-host.internal", "corrupt_port": 9999},
    )

    initial_resp = client.post(
        "/workflow/run",
        json={
            "incident_description": "Supervised mode approve-and-execute test",
            "autonomy_mode": "supervised",
            "force_fallback": True,
        },
    )
    paused_state = initial_resp.json()
    assert paused_state["status"] == "AWAITING_APPROVAL"

    # Operator approves execution
    resume_resp = client.post(
        "/workflow/resume",
        json={
            "approved": True,
            "paused_state": paused_state,
        },
    )
    assert resume_resp.status_code == 200
    resumed_data = resume_resp.json()

    assert resumed_data["status"] == "SUCCESS"
    assert resumed_data["human_approved"] is True
    assert resumed_data["execution_result"] is not None
    assert resumed_data["verification_result"]["verified"] is True

    # Service successfully restored
    assert active_config.db_port == 5432


# ---------------------------------------------------------------------------
# 3. Autonomous Mode Tests
# ---------------------------------------------------------------------------


def test_autonomous_mode_automatically_executes_safe_action(client):
    """
    Autonomous Mode:
    - Safe, allowlisted actions execute without human intervention.
    """
    fault_manager.inject(FaultType.DB_UNAVAILABLE)

    resp = client.post(
        "/workflow/run",
        json={
            "incident_description": "Autonomous DB outage recovery",
            "autonomy_mode": "autonomous",
            "force_fallback": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "SUCCESS"
    assert data["execution_result"]["action_type"] == "reconnect_database"
    assert data["verification_result"]["verified"] is True
    assert not fault_manager.is_active(FaultType.DB_UNAVAILABLE)


# ---------------------------------------------------------------------------
# 4. Safety Rejection Scenarios (Across All Modes)
# ---------------------------------------------------------------------------


def test_safety_rejection_destructive_action():
    """Destructive action (drop database) must be mathematically blocked."""
    proposal = ActionProposal(
        action_type="drop_table_appointments",
        parameters={"table": "appointments"},
        rationale="Clear corrupted table",
        supporting_evidence=["db_error"],
    )
    decision = validate_recovery_proposal(proposal)
    assert decision.approved is False
    assert decision.requires_human_escalation is True
    assert "forbidden" in decision.reason.lower() or "pre-approved" in decision.reason.lower() or "destructive" in decision.reason.lower()


def test_safety_rejection_unknown_action():
    """Non-allowlisted arbitrary action is rejected."""
    proposal = ActionProposal(
        action_type="curl_remote_exploit_script",
        parameters={},
        rationale="External script repair",
        supporting_evidence=[],
    )
    decision = validate_recovery_proposal(proposal)
    assert decision.approved is False
    assert decision.requires_human_escalation is True


def test_safety_rejection_insufficient_evidence():
    """Allowlisted action proposed without matching evidence is rejected."""
    proposal = ActionProposal(
        action_type="reconnect_database",
        parameters={},
        rationale="Proactive reconnect",
        supporting_evidence=["unrelated_metric"],
    )
    decision = validate_recovery_proposal(proposal)
    assert decision.approved is False
    assert "diagnostic evidence" in decision.reason.lower()


def test_safety_rejection_retry_limit_exhausted():
    """Attempt count exceeding 3 is immediately rejected by governor."""
    proposal = ActionProposal(
        action_type="restore_baseline_config",
        parameters={},
        rationale="Retry 4",
        supporting_evidence=["config_divergence"],
        attempt_number=4,  # Exceeds max 3
    )
    decision = validate_recovery_proposal(proposal)
    assert decision.approved is False
    assert "maximum recovery attempts" in decision.reason.lower()


def test_end_to_end_unsafe_action_scenario_injection_and_governor_block(client):
    """
    Scenario 4: Injecting unsafe_proposal_sim via API.
    - Fault inject endpoint succeeds with 200 OK.
    - Autonomous workflow runs.
    - AI planner recommends drop_table_appointments.
    - Safety Governor intercepts and rejects the proposal.
    - Workflow escalates without modifying the simulator.
    """
    inject_resp = client.post(
        "/simulator/faults/inject",
        json={"fault_type": "unsafe_proposal_sim", "params": {}},
    )
    assert inject_resp.status_code == 200
    assert "unsafe_proposal_sim" in inject_resp.json()["active_faults"]

    # Run workflow
    run_resp = client.post(
        "/workflow/run",
        json={
            "incident_description": "Testing rogue AI proposal injection",
            "autonomy_mode": "autonomous",
            "force_fallback": True,
        },
    )
    assert run_resp.status_code == 200
    data = run_resp.json()

    assert data["status"] == "ESCALATED"
    assert data["planner_recommendation"]["recovery_action"] == "drop_table_appointments"
    assert data["governor_decision"]["approved"] is False
    assert data["governor_decision"]["requires_human_escalation"] is True
    assert data["execution_result"] is None
