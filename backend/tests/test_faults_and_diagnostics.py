"""
Tests for Phase 3 — Fault Injection and Diagnostic Tools.

Verifies:
  - Injection and reset of operational faults (invalid_db_config, db_unavailable, high_latency).
  - Diagnostic tools return structured evidence matching system state.
  - Deterministic safety governor rejects unsafe action proposals.
  - Fault state resets cleanly without leakage between runs.
"""

import pytest
from fastapi.testclient import TestClient

from app.diagnostics.models import DiagnosticReport
from app.diagnostics.tools import (
    check_database_status,
    check_service_health,
    compare_configuration,
    get_recent_logs,
    measure_latency,
    run_all_diagnostics,
)
from app.main import app
from app.simulator.config import BASELINE_CONFIG, active_config
from app.simulator.faults import fault_manager
from app.simulator.models import (
    FaultType,
    ProposedAction,
    ProposedActionType,
    validate_proposed_action,
)


@pytest.fixture(autouse=True)
def clean_simulator_state():
    """Ensure every test starts and ends with a clean simulator state."""
    fault_manager.reset()
    yield
    fault_manager.reset()


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Baseline / Healthy State Diagnostics
# ---------------------------------------------------------------------------


def test_baseline_diagnostics_healthy():
    """When no faults are active, all diagnostics should report healthy status."""
    health = check_service_health()
    assert health.is_healthy is True
    assert health.status == "healthy"

    db = check_database_status()
    assert db.is_reachable is True
    assert db.status_code == "CONNECTED"
    assert db.error_detail is None

    config = compare_configuration()
    assert config.has_divergence is False
    assert len(config.divergent_keys) == 0

    latency = measure_latency()
    assert latency.sla_violated is False
    assert latency.avg_latency_ms < latency.threshold_ms


# ---------------------------------------------------------------------------
# 2. Fault 1: Invalid Database Configuration
# ---------------------------------------------------------------------------


def test_fault_invalid_db_config(client):
    """
    Inject invalid database config.
    Config diagnostic must detect divergence and DB status must report failure.
    """
    # Inject fault via API
    resp = client.post(
        "/simulator/faults/inject",
        json={
            "fault_type": "invalid_db_config",
            "params": {"corrupt_host": "wrong-db.internal", "corrupt_port": 9999},
        },
    )
    assert resp.status_code == 200
    assert "invalid_db_config" in resp.json()["active_faults"]

    # Verify Configuration Diagnostic identifies the discrepancy
    config_evidence = compare_configuration()
    assert config_evidence.has_divergence is True
    assert "db_host" in config_evidence.divergent_keys
    assert "db_port" in config_evidence.divergent_keys

    # Verify Database Diagnostic flags reachability failure
    db_evidence = check_database_status()
    assert db_evidence.is_reachable is False
    assert db_evidence.status_code == "UNKNOWN_HOST_OR_PORT"
    assert "wrong-db.internal" in (db_evidence.error_detail or "")

    # Booking attempt under this fault must be rejected
    booking_resp = client.post(
        "/clinic/book",
        json={
            "patient_id": "P-1001",
            "doctor_id": "D-101",
            "date": "2025-04-01",
            "time": "09:00",
            "reason": "Routine",
        },
    )
    assert booking_resp.json()["success"] is False
    assert "Database host unreachable" in booking_resp.json()["message"]

    # Reset fault
    reset_resp = client.post("/simulator/faults/reset")
    assert reset_resp.status_code == 200
    assert len(reset_resp.json()["active_faults"]) == 0

    # Ensure baseline restored
    assert compare_configuration().has_divergence is False
    assert check_database_status().is_reachable is True


# ---------------------------------------------------------------------------
# 3. Fault 2: Database Unavailable
# ---------------------------------------------------------------------------


def test_fault_db_unavailable(client):
    """
    Inject database outage.
    Service must report DOWN and DB diagnostic must report connection refused.
    """
    client.post(
        "/simulator/faults/inject",
        json={"fault_type": "db_unavailable"},
    )

    # Health must report DOWN
    health = check_service_health()
    assert health.is_healthy is False
    assert health.status == "down"

    # Database diagnostic must identify connection refused
    db_evidence = check_database_status()
    assert db_evidence.is_reachable is False
    assert db_evidence.status_code == "CONNECTION_REFUSED"

    # Booking must be refused
    booking_resp = client.post(
        "/clinic/book",
        json={
            "patient_id": "P-1001",
            "doctor_id": "D-101",
            "date": "2025-04-01",
            "time": "09:00",
            "reason": "Routine",
        },
    )
    assert booking_resp.json()["success"] is False
    assert "Database unavailable" in booking_resp.json()["message"]

    # Reset fault
    client.post("/simulator/faults/reset")
    assert check_service_health().is_healthy is True


# ---------------------------------------------------------------------------
# 4. Fault 3: High Latency
# ---------------------------------------------------------------------------


def test_fault_high_latency(client):
    """
    Inject 3000ms latency overhead.
    Latency diagnostic must flag SLA violation.
    """
    client.post(
        "/simulator/faults/inject",
        json={
            "fault_type": "high_latency",
            "params": {"added_latency_ms": 3000},
        },
    )

    # Latency diagnostic must detect SLA violation (> 200ms threshold)
    latency_evidence = measure_latency(samples=3)
    assert latency_evidence.sla_violated is True
    assert latency_evidence.avg_latency_ms > 2500.0

    # Health diagnostic marks service degraded
    health = check_service_health()
    assert health.status == "degraded"

    # Reset fault
    client.post("/simulator/faults/reset")
    assert measure_latency().sla_violated is False


# ---------------------------------------------------------------------------
# 5. Diagnostic Report Consolidation
# ---------------------------------------------------------------------------


def test_consolidated_diagnostic_report_endpoint(client):
    """GET /diagnostics/report must return all 5 diagnostic sections."""
    resp = client.get("/diagnostics/report")
    assert resp.status_code == 200
    report = DiagnosticReport(**resp.json())
    assert report.service_health is not None
    assert report.database is not None
    assert report.configuration is not None
    assert report.latency is not None
    assert report.logs is not None


# ---------------------------------------------------------------------------
# 6. Safety Governor: Rejection of Unsafe Proposals
# ---------------------------------------------------------------------------


def test_safety_governor_rejects_unsafe_proposals():
    """
    Deliberately unsafe proposals like DROP_DATABASE or RUN_SHELL_COMMAND
    must be strictly rejected by deterministic Python validation.
    """
    unsafe_proposal = ProposedAction(
        action_type=ProposedActionType.DROP_DATABASE,
        parameters={"cascade": True},
        rationale="Clear the database to fix data inconsistency.",
    )
    result = validate_proposed_action(unsafe_proposal)
    assert result.is_safe is False
    assert result.rejected is True
    assert result.requires_human_escalation is True
    assert "FORBIDDEN" in result.reason


def test_safety_governor_allows_approved_repair_actions():
    """
    Allowlisted recovery actions like RESTORE_BASELINE_CONFIG must be approved.
    """
    safe_proposal = ProposedAction(
        action_type=ProposedActionType.RESTORE_BASELINE_CONFIG,
        parameters={},
        rationale="Revert configuration drift back to known golden baseline.",
    )
    result = validate_proposed_action(safe_proposal)
    assert result.is_safe is True
    assert result.rejected is False
    assert result.requires_human_escalation is False

