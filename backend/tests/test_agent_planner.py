"""
Tests for Phase 5 — LLM Investigator and Repair Planner.

Verifies:
  - Output schema validation strictly rejects malformed model output.
  - Deterministic fallback mode operates correctly without live API dependencies.
  - Planner correctly identifies root causes and proposes matching allowlisted recovery actions.
  - Endpoints /agent/plan and /agent/status function cleanly.
  - Automated tests do not depend on external network or live LLM calls.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.agent.fallback import fallback_planner
from app.agent.models import (
    DiagnosticToolName,
    PlannerDecisionType,
    PlannerRecommendation,
)
from app.agent.planner import investigation_planner
from app.main import app
from app.recovery.models import RecoveryActionType
from app.simulator.faults import fault_manager
from app.simulator.models import FaultType


@pytest.fixture(autouse=True)
def clean_state():
    """Ensure simulator state is clean before and after every test."""
    fault_manager.reset()
    yield
    fault_manager.reset()


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Output Schema Validation Tests (Preventing Model Hallucinations)
# ---------------------------------------------------------------------------


def test_planner_recommendation_schema_valid():
    """Valid recommendation data parses cleanly into Pydantic model."""
    rec = PlannerRecommendation(
        decision_type=PlannerDecisionType.RECOVER,
        diagnostic_tool=None,
        recovery_action=RecoveryActionType.RESTORE_BASELINE_CONFIG.value,
        parameters={},
        hypothesis="Database host changed from golden baseline.",
        rationale="Configuration diagnostic detected divergent host key.",
        supporting_evidence=["config_divergence"],
        confidence_score=0.95,
        source="DETERMINISTIC_FALLBACK",
    )
    assert rec.decision_type == PlannerDecisionType.RECOVER
    assert rec.recovery_action == "restore_baseline_config"
    assert rec.confidence_score == 0.95


def test_schema_rejects_invalid_decision_type():
    """Invalid decision type strings must fail validation."""
    with pytest.raises(ValidationError):
        PlannerRecommendation(
            decision_type="ARBITRARY_DECISION",  # Invalid!
            hypothesis="Test",
            rationale="Test",
            confidence_score=0.5,
        )


def test_schema_rejects_out_of_bound_confidence():
    """Confidence scores outside [0.0, 1.0] must be rejected."""
    with pytest.raises(ValidationError):
        PlannerRecommendation(
            decision_type=PlannerDecisionType.RECOVER,
            hypothesis="Test",
            rationale="Test",
            confidence_score=1.5,  # Exceeds max 1.0!
        )

    with pytest.raises(ValidationError):
        PlannerRecommendation(
            decision_type=PlannerDecisionType.RECOVER,
            hypothesis="Test",
            rationale="Test",
            confidence_score=-0.1,  # Below min 0.0!
        )


# ---------------------------------------------------------------------------
# 2. Deterministic Planner Tests for Every Incident Scenario
# ---------------------------------------------------------------------------


def test_planner_recommends_restore_baseline_on_config_drift():
    """When config fault is injected, planner recommends restore_baseline_config."""
    fault_manager.inject(
        FaultType.INVALID_DB_CONFIG,
        {"corrupt_host": "bad-host.internal", "corrupt_port": 9999},
    )
    rec = fallback_planner.plan()

    assert rec.decision_type == PlannerDecisionType.RECOVER
    assert rec.recovery_action == RecoveryActionType.RESTORE_BASELINE_CONFIG.value
    assert "config_divergence" in rec.supporting_evidence
    assert rec.confidence_score >= 0.90


def test_planner_recommends_reconnect_database_on_socket_outage():
    """When database is unavailable, planner recommends reconnect_database."""
    fault_manager.inject(FaultType.DB_UNAVAILABLE)
    rec = fallback_planner.plan()

    assert rec.decision_type == PlannerDecisionType.RECOVER
    assert rec.recovery_action == RecoveryActionType.RECONNECT_DATABASE.value
    assert "db_unavailable" in rec.supporting_evidence
    assert rec.confidence_score >= 0.90


def test_planner_recommends_clear_latency_on_sla_breach():
    """When latency overhead is injected, planner recommends clear_latency_delay."""
    fault_manager.inject(
        FaultType.HIGH_LATENCY,
        {"added_latency_ms": 3000},
    )
    rec = fallback_planner.plan()

    assert rec.decision_type == PlannerDecisionType.RECOVER
    assert rec.recovery_action == RecoveryActionType.CLEAR_LATENCY_DELAY.value
    assert "high_latency" in rec.supporting_evidence


def test_planner_declares_no_action_on_healthy_system():
    """On a baseline healthy system, planner recommends NO_ACTION."""
    rec = fallback_planner.plan()
    assert rec.decision_type == PlannerDecisionType.NO_ACTION
    assert rec.recovery_action is None
    assert rec.confidence_score == 1.0


# ---------------------------------------------------------------------------
# 3. InvestigationPlanner Fallback & Error Handling Tests
# ---------------------------------------------------------------------------


def test_investigation_planner_forces_fallback():
    """InvestigationPlanner with force_fallback=True uses fallback cleanly."""
    fault_manager.inject(FaultType.DB_UNAVAILABLE)
    rec = investigation_planner.plan(force_fallback=True)

    assert rec.decision_type == PlannerDecisionType.RECOVER
    assert rec.recovery_action == "reconnect_database"
    assert rec.source == "DETERMINISTIC_FALLBACK"


def test_investigation_planner_status_endpoint(client):
    """GET /agent/status reports active status and available tools/actions."""
    resp = client.get("/agent/status")
    assert resp.status_code == 200
    status = resp.json()

    assert "has_api_key" in status
    assert "model_name" in status
    assert "available_diagnostic_tools" in status
    assert "allowed_recovery_actions" in status
    assert "restore_baseline_config" in status["allowed_recovery_actions"]


def test_api_endpoint_plan_with_fallback(client):
    """POST /agent/plan?force_fallback=true returns a structured recommendation."""
    fault_manager.inject(
        FaultType.INVALID_DB_CONFIG,
        {"corrupt_host": "wrong.domain", "corrupt_port": 8000},
    )
    resp = client.post("/agent/plan?force_fallback=true")
    assert resp.status_code == 200
    data = resp.json()

    assert data["decision_type"] == "RECOVER"
    assert data["recovery_action"] == "restore_baseline_config"
    assert "config_divergence" in data["supporting_evidence"]
    assert data["source"] == "DETERMINISTIC_FALLBACK"

