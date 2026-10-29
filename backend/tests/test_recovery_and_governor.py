"""
Tests for Phase 4 — Safe Recovery Actions, Safety Governor, Verification, and Audit Timeline.

Verifies:
  - Only allowlisted actions execute.
  - Destructive / non-allowlisted actions are rejected and escalated.
  - Dangerous parameters are detected and blocked.
  - Recovery attempts are bounded (max 3).
  - Unjustified actions lacking diagnostic evidence are rejected.
  - Verification fails if the fault is not genuinely resolved.
  - End-to-end recovery cycle executes, verifies, and records full audit trail.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.recovery.governor import validate_recovery_proposal
from app.recovery.models import (
    ActionProposal,
    AuditStage,
    RecoveryActionType,
)
from app.recovery.timeline import audit_timeline
from app.recovery.verifier import verify_system_recovery
from app.simulator.faults import fault_manager
from app.simulator.models import FaultType


@pytest.fixture(autouse=True)
def clean_state():
    """Ensure clean simulator state and clean audit timeline for every test."""
    fault_manager.reset()
    audit_timeline.clear()
    yield
    fault_manager.reset()
    audit_timeline.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Allowlist & Unsafe Action Tests
# ---------------------------------------------------------------------------


def test_governor_rejects_drop_database():
    """Destructive action DROP_DATABASE must be rejected and flagged for escalation."""
    proposal = ActionProposal(
        action_type=RecoveryActionType.DROP_DATABASE.value,
        parameters={"table": "patients"},
        rationale="Wipe corrupt table to recover.",
        supporting_evidence=["db_error"],
        attempt_number=1,
    )
    decision = validate_recovery_proposal(proposal)
    assert decision.approved is False
    assert decision.requires_human_escalation is True
    assert "FORBIDDEN" in decision.reason


def test_governor_rejects_arbitrary_shell_command():
    """Arbitrary shell commands must be strictly rejected."""
    proposal = ActionProposal(
        action_type=RecoveryActionType.RUN_SHELL_COMMAND.value,
        parameters={"cmd": "rm -rf /"},
        rationale="Clear disk space.",
        supporting_evidence=["disk_error"],
        attempt_number=1,
    )
    decision = validate_recovery_proposal(proposal)
    assert decision.approved is False
    assert decision.requires_human_escalation is True
    assert "FORBIDDEN" in decision.reason


def test_governor_rejects_unknown_action_string():
    """Any unrecognized action name is forbidden."""
    proposal = ActionProposal(
        action_type="random_script_execution",
        parameters={},
        rationale="Try something random.",
        supporting_evidence=["unknown"],
        attempt_number=1,
    )
    decision = validate_recovery_proposal(proposal)
    assert decision.approved is False
    assert decision.requires_human_escalation is True


# ---------------------------------------------------------------------------
# 2. Parameter & Evidence Guardrail Tests
# ---------------------------------------------------------------------------


def test_governor_rejects_dangerous_parameters_in_allowlisted_action():
    """Even an allowlisted action is rejected if dangerous parameters are present."""
    proposal = ActionProposal(
        action_type=RecoveryActionType.RESTORE_BASELINE_CONFIG.value,
        parameters={"force": "true", "delete_backups": "true"},
        rationale="Force restore and wipe backups.",
        supporting_evidence=["config_divergence"],
        attempt_number=1,
    )
    decision = validate_recovery_proposal(proposal)
    assert decision.approved is False
    assert "dangerous parameter" in decision.reason


def test_governor_rejects_missing_evidence():
    """Actions without diagnostic evidence must be rejected."""
    proposal = ActionProposal(
        action_type=RecoveryActionType.RESTORE_BASELINE_CONFIG.value,
        parameters={},
        rationale="Guessing config might be wrong.",
        supporting_evidence=[],  # Missing!
        attempt_number=1,
    )
    decision = validate_recovery_proposal(proposal)
    assert decision.approved is False
    assert "No supporting diagnostic evidence provided" in decision.reason


def test_governor_rejects_mismatched_evidence():
    """Actions must correlate with the observed symptoms."""
    proposal = ActionProposal(
        action_type=RecoveryActionType.CLEAR_LATENCY_DELAY.value,
        parameters={},
        rationale="Clear latency even though symptom is config error.",
        supporting_evidence=["unknown_host"],  # Unrelated to latency!
        attempt_number=1,
    )
    decision = validate_recovery_proposal(proposal)
    assert decision.approved is False
    assert "does not address the supplied diagnostic evidence" in decision.reason


# ---------------------------------------------------------------------------
# 3. Bounded Retry Count Test
# ---------------------------------------------------------------------------


def test_governor_enforces_max_attempts_limit():
    """Attempt 4 exceeds the limit of 3 and must be blocked and escalated."""
    proposal = ActionProposal(
        action_type=RecoveryActionType.RESTORE_BASELINE_CONFIG.value,
        parameters={},
        rationale="Fourth retry attempt.",
        supporting_evidence=["config_divergence"],
        attempt_number=4,
    )
    decision = validate_recovery_proposal(proposal)
    assert decision.approved is False
    assert decision.requires_human_escalation is True
    assert "Maximum recovery attempts" in decision.reason


# ---------------------------------------------------------------------------
# 4. Verification Probe Tests
# ---------------------------------------------------------------------------


def test_verification_probe_passes_on_healthy_system():
    """On a clean baseline system, all 4 verification checks pass."""
    result = verify_system_recovery()
    assert result.verified is True
    assert result.health_ok is True
    assert result.database_ok is True
    assert result.latency_ok is True
    assert result.booking_test_ok is True
    assert "Verification PASSED" in result.details


def test_verification_probe_fails_when_fault_is_active():
    """If a database fault is active, verification probe detects it and fails."""
    fault_manager.inject(FaultType.DB_UNAVAILABLE)
    result = verify_system_recovery()
    assert result.verified is False
    assert result.health_ok is False
    assert result.database_ok is False
    assert "Verification FAILED" in result.details


# ---------------------------------------------------------------------------
# 5. Full End-to-End Recovery Cycle & Timeline Audit Tests
# ---------------------------------------------------------------------------


def test_full_successful_recovery_cycle(client):
    """
    Simulate full incident lifecycle:
    1. Fault injected: invalid database config.
    2. Agent proposes safe action: restore_baseline_config with supporting evidence.
    3. Safety governor validates and approves.
    4. Action executes on simulator.
    5. Post-recovery verification suite runs and passes.
    6. Audit timeline records all 4 milestones.
    """
    # Step 1: Inject fault
    fault_manager.inject(
        FaultType.INVALID_DB_CONFIG,
        {"corrupt_host": "unreachable.db", "corrupt_port": 9000},
    )

    # Step 2 & 3 & 4 & 5: Propose and execute recovery
    payload = {
        "action_type": "restore_baseline_config",
        "parameters": {},
        "rationale": "Configuration comparison showed db_host divergence.",
        "supporting_evidence": ["config_divergence", "unknown_host"],
        "attempt_number": 1,
    }
    resp = client.post("/recovery/propose-and-execute", json=payload)
    assert resp.status_code == 200
    outcome = resp.json()

    assert outcome["overall_status"] == "SUCCESS"
    assert outcome["governor_decision"]["approved"] is True
    assert outcome["execution_result"]["executed"] is True
    assert outcome["verification_result"]["verified"] is True
    assert outcome["verification_result"]["booking_test_ok"] is True

    # Step 6: Verify Audit Timeline contains chronological audit stages
    timeline_resp = client.get("/recovery/timeline")
    assert timeline_resp.status_code == 200
    timeline = timeline_resp.json()

    stages = [entry["stage"] for entry in timeline]
    assert "PROPOSED" in stages
    assert "SAFETY_CHECK" in stages
    assert "EXECUTED" in stages
    assert "VERIFIED" in stages


def test_rejected_recovery_cycle_logs_to_timeline(client):
    """
    When an unsafe action is proposed:
    - Status is REJECTED or ESCALATED.
    - No execution takes place.
    - Timeline documents the rejection and escalation.
    """
    payload = {
        "action_type": "delete_all_patients",
        "parameters": {},
        "rationale": "Reset all data to fix corruption.",
        "supporting_evidence": ["data_error"],
        "attempt_number": 1,
    }
    resp = client.post("/recovery/propose-and-execute", json=payload)
    assert resp.status_code == 200
    outcome = resp.json()

    assert outcome["overall_status"] == "ESCALATED"
    assert outcome["governor_decision"]["approved"] is False
    assert outcome["execution_result"] is None
    assert outcome["verification_result"] is None

    # Audit timeline check
    timeline = client.get("/recovery/timeline").json()
    stages = [entry["stage"] for entry in timeline]
    assert "PROPOSED" in stages
    assert "SAFETY_CHECK" in stages
    assert "REJECTED" in stages
    assert "ESCALATED" in stages
    assert "EXECUTED" not in stages

