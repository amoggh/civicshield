"""
Deterministic Fallback Planner.

Provides a robust, zero-network rule-based planner that runs when:
1. No Google Gemini API key is configured.
2. Network connectivity to Gemini fails or times out.
3. Automated unit tests run without live API dependencies.

Analyzes structured diagnostic evidence and selects the appropriate tool or recovery action.
"""

from datetime import datetime, timezone
import logging

from app.diagnostics.models import DiagnosticReport
from app.diagnostics.tools import run_all_diagnostics
from app.recovery.models import RecoveryActionType

from .models import (
    DiagnosticToolName,
    PlannerDecisionType,
    PlannerRecommendation,
)

logger = logging.getLogger("civicshield.agent.fallback")


class DeterministicFallbackPlanner:
    """
    Deterministic rule engine mirroring the LLM planner's reasoning path.
    Guarantees the system operates smoothly in offline, air-gapped, or test environments.
    """

    def plan(self, report: DiagnosticReport | None = None) -> PlannerRecommendation:
        """
        Analyze diagnostic report and return a validated PlannerRecommendation.
        If no report is provided, collects fresh evidence across all diagnostic tools.
        """
        if report is None:
            report = run_all_diagnostics()

        now = datetime.now(timezone.utc)

        # Rule 1: Configuration Divergence
        if report.configuration.has_divergence:
            keys_str = ", ".join(report.configuration.divergent_keys)
            return PlannerRecommendation(
                decision_type=PlannerDecisionType.RECOVER,
                diagnostic_tool=None,
                recovery_action=RecoveryActionType.RESTORE_BASELINE_CONFIG.value,
                parameters={},
                hypothesis=f"Configuration drift detected on keys: {keys_str}.",
                rationale=(
                    f"compare_configuration() reported divergence on {keys_str}. "
                    "Restoring baseline golden configuration eliminates configuration errors."
                ),
                supporting_evidence=["config_divergence", "unknown_host", *report.configuration.divergent_keys],
                confidence_score=0.95,
                source="DETERMINISTIC_FALLBACK",
                generated_at=now,
            )

        # Rule 2: Database Connection Outage
        if not report.database.is_reachable:
            if report.database.status_code == "CONNECTION_REFUSED":
                return PlannerRecommendation(
                    decision_type=PlannerDecisionType.RECOVER,
                    diagnostic_tool=None,
                    recovery_action=RecoveryActionType.RECONNECT_DATABASE.value,
                    parameters={},
                    hypothesis="Simulated database server is unreachable (connection refused).",
                    rationale=(
                        "check_database_status() reported CONNECTION_REFUSED on port 5432. "
                        "Re-establishing database connection restores dependency availability."
                    ),
                    supporting_evidence=["db_unavailable", "connection_refused", "database"],
                    confidence_score=0.95,
                    source="DETERMINISTIC_FALLBACK",
                    generated_at=now,
                )

        # Rule 3: Latency SLA Violation
        if report.latency.sla_violated:
            return PlannerRecommendation(
                decision_type=PlannerDecisionType.RECOVER,
                diagnostic_tool=None,
                recovery_action=RecoveryActionType.CLEAR_LATENCY_DELAY.value,
                parameters={},
                hypothesis=(
                    f"Latency SLA violated: average {report.latency.avg_latency_ms}ms "
                    f"exceeds threshold of {report.latency.threshold_ms}ms."
                ),
                rationale=(
                    "measure_latency() detected severe artificial latency overhead. "
                    "Clearing simulated latency delay restores healthy throughput."
                ),
                supporting_evidence=["high_latency", "latency_violation", "timeout"],
                confidence_score=0.90,
                source="DETERMINISTIC_FALLBACK",
                generated_at=now,
            )

        # Rule 4: Service Unhealthy but specific cause not yet isolated
        if not report.service_health.is_healthy:
            return PlannerRecommendation(
                decision_type=PlannerDecisionType.INVESTIGATE,
                diagnostic_tool=DiagnosticToolName.CHECK_DATABASE_STATUS,
                recovery_action=None,
                parameters={},
                hypothesis="Service health degraded/down, but root cause requires deeper investigation.",
                rationale="Service reported unhealthy. Probing database reachability to inspect socket connectivity.",
                supporting_evidence=["service_degraded"],
                confidence_score=0.70,
                source="DETERMINISTIC_FALLBACK",
                generated_at=now,
            )

        # Rule 5: Healthy State
        return PlannerRecommendation(
            decision_type=PlannerDecisionType.NO_ACTION,
            diagnostic_tool=None,
            recovery_action=None,
            parameters={},
            hypothesis="All diagnostic probes confirm the clinic service is fully operational.",
            rationale="Service health, database, configuration, and latency all satisfy healthy baselines.",
            supporting_evidence=["healthy_baseline"],
            confidence_score=1.0,
            source="DETERMINISTIC_FALLBACK",
            generated_at=now,
        )


# Global singleton fallback planner
fallback_planner = DeterministicFallbackPlanner()

