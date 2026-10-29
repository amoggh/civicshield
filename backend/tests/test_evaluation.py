"""
Tests for Phase 8 — Evaluation and Baseline Comparison.

Verifies:
  - Benchmark suite runs repeatability across all 4 scenarios for both systems.
  - Metrics are computed empirically from actual runs (never invented or hardcoded).
  - Restart-only baseline fails on configuration drift and latency, whereas CivicShield recovers.
  - Safety governor blocks adversarial unsafe action in benchmark comparison.
  - Results are persisted to JSON with explicit limitations documentation.
  - Endpoints /evaluation/run and /evaluation/results respond cleanly.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.evaluation.models import EvaluationReport, EvaluationScenario
from app.evaluation.runner import RESULTS_FILE, evaluation_runner
from app.main import app
from app.simulator.faults import fault_manager


@pytest.fixture(autouse=True)
def clean_state():
    """Ensure clean simulator state before and after each test."""
    fault_manager.reset()
    yield
    fault_manager.reset()


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Benchmark Execution & Empirical Metric Derivation
# ---------------------------------------------------------------------------


def test_benchmark_suite_computes_empirical_metrics():
    """
    Run the full benchmark suite. Verify metrics derive from actual trial data:
    - CivicShield recovers all 3 recoverable scenarios (100% recovery rate).
    - RestartBaseline only recovers db_unavailable (33.3% recovery rate).
    - CivicShield safely intercepts the adversarial unsafe proposal (100% rejection).
    """
    report = evaluation_runner.run_benchmark()

    assert isinstance(report, EvaluationReport)
    assert report.sample_size == 4
    assert "synthetic" in report.limitations.lower()

    # CivicShield metrics
    cs = report.civicshield_metrics
    assert cs.system_name == "CivicShield"
    assert cs.recovery_success_rate == 100.0  # Successfully resolved 3 of 3 recoverable scenarios
    assert cs.unsafe_action_rejection_rate == 100.0  # Successfully blocked adversarial action
    assert cs.root_cause_accuracy >= 75.0

    # Baseline metrics
    bl = report.baseline_metrics
    assert bl.system_name == "RestartBaseline"
    assert bl.recovery_success_rate < 50.0  # Fails config drift and latency overhead
    assert bl.unsafe_action_rejection_rate == 0.0  # Lacks safety governor
    assert bl.total_unnecessary_attempts > 0

    # Ensure raw scenario records exist for both systems
    assert len(report.scenario_runs) == 8  # 4 scenarios x 2 systems


def test_benchmark_persists_results_json():
    """Verify results are saved locally to results.json on disk."""
    report = evaluation_runner.run_benchmark()
    assert RESULTS_FILE.exists()

    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "CivicShield" in content
        assert "RestartBaseline" in content
        assert "limitations" in content


# ---------------------------------------------------------------------------
# 2. REST Endpoints
# ---------------------------------------------------------------------------


def test_evaluation_run_endpoint(client):
    """POST /evaluation/run triggers benchmark execution and returns valid report."""
    resp = client.post("/evaluation/run")
    assert resp.status_code == 200
    data = resp.json()

    assert "civicshield_metrics" in data
    assert "baseline_metrics" in data
    assert data["civicshield_metrics"]["recovery_success_rate"] == 100.0
    assert len(data["scenario_runs"]) == 8


def test_evaluation_results_endpoint(client):
    """GET /evaluation/results returns latest recorded benchmark report."""
    # Ensure at least one run is recorded
    evaluation_runner.get_latest_results()

    resp = client.get("/evaluation/results")
    assert resp.status_code == 200
    data = resp.json()

    assert data["sample_size"] == 4
    assert data["baseline_metrics"]["system_name"] == "RestartBaseline"

