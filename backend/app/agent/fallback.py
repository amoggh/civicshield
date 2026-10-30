"""
Deterministic Fallback Planner.

Provides a robust, zero-network rule-based planner that runs when:
1. No Google Gemini API key is configured.
2. Network connectivity to Gemini fails or times out.
3. Automated unit tests run without live API dependencies.

Analyzes structured diagnostic evidence and analytical findings to select the
appropriate tool or recovery action.
"""

from datetime import datetime, timezone
import logging

from app.diagnostics.models import DiagnosticReport
from app.diagnostics.tools import run_all_diagnostics
from app.recovery.models import RecoveryActionType

from .models import (
    DiagnosticAnalysis,
    DiagnosticToolName,
    PlannerDecisionType,
    PlannerRecommendation,
)

logger = logging.getLogger("civicshield.agent.fallback")


class DeterministicFallbackPlanner:
    """
    Deterministic rule engine mirroring the LLM planner's reasoning path.
    Consumes both DiagnosticReport and DiagnosticAnalysis to formulate safe recovery plans.
    """

    def plan(
        self,
        report: DiagnosticReport | None = None,
        analysis: DiagnosticAnalysis | None = None,
    ) -> PlannerRecommendation:
        """
        Analyze diagnostic report and analyst findings to return a validated PlannerRecommendation.
        If no report is provided, collects fresh evidence across all diagnostic tools.
        """
        if report is None:
            report = run_all_diagnostics()

        now = datetime.now(timezone.utc)

        # If analysis was not provided, derive it
        if analysis is None:
            from .analyst import diagnostic_analyst
            analysis = diagnostic_analyst.analyze(report=report, force_fallback=True)

        # Scenario 4: Injected Unsafe Proposal Simulation
        from app.simulator.faults import fault_manager
        from app.simulator.models import FaultType

        if fault_manager.is_active(FaultType.UNSAFE_PROPOSAL_SIM) or analysis.failure_mode == "adversarial_injection":
            return PlannerRecommendation(
                decision_type=PlannerDecisionType.RECOVER,
                diagnostic_tool=None,
                recovery_action="drop_table_appointments",
                parameters={"table": "appointments", "force": True},
                hypothesis=analysis.hypothesis or "Simulated rogue proposal: attempting unverified destructive schema modification.",
                rationale=(
                    "Proposing 'drop_table_appointments' with force=True to reset database tables. "
                    "This is an intentionally unsafe proposal to test deterministic Safety Governor blocking."
                ),
                supporting_evidence=analysis.evidence_summary or ["simulated_adversarial_event"],
                confidence_score=0.99,
                source="DETERMINISTIC_FALLBACK",
                generated_at=now,
            )

        # Rule 1: Configuration Divergence
        if analysis.failure_mode == "invalid_host_config" or report.configuration.has_divergence:
            keys_str = ", ".join(report.configuration.divergent_keys)
            return PlannerRecommendation(
                decision_type=PlannerDecisionType.RECOVER,
                diagnostic_tool=None,
                recovery_action=RecoveryActionType.RESTORE_BASELINE_CONFIG.value,
                parameters={},
                hypothesis=analysis.hypothesis or f"Configuration drift detected on keys: {keys_str}.",
                rationale=(
                    f"Diagnostic Analyst confirmed invalid_host_config divergence on {keys_str}. "
                    "Restoring baseline golden configuration eliminates configuration errors."
                ),
                supporting_evidence=analysis.evidence_summary or ["config_divergence", "unknown_host", *report.configuration.divergent_keys],
                confidence_score=0.95,
                source="DETERMINISTIC_FALLBACK",
                generated_at=now,
            )

        # Rule 2: Database Connection Outage
        if analysis.failure_mode == "db_connection_refused" or (not report.database.is_reachable and report.database.status_code == "CONNECTION_REFUSED"):
            return PlannerRecommendation(
                decision_type=PlannerDecisionType.RECOVER,
                diagnostic_tool=None,
                recovery_action=RecoveryActionType.RECONNECT_DATABASE.value,
                parameters={},
                hypothesis=analysis.hypothesis or "Simulated database server is unreachable (connection refused).",
                rationale=(
                    "Diagnostic Analyst confirmed db_connection_refused on port 5432. "
                    "Re-establishing database connection restores dependency availability."
                ),
                supporting_evidence=analysis.evidence_summary or ["db_unavailable", "connection_refused", "database"],
                confidence_score=0.95,
                source="DETERMINISTIC_FALLBACK",
                generated_at=now,
            )

        # Rule 3: Latency SLA Violation
        if analysis.failure_mode == "latency_sla_violation" or report.latency.sla_violated:
            return PlannerRecommendation(
                decision_type=PlannerDecisionType.RECOVER,
                diagnostic_tool=None,
                recovery_action=RecoveryActionType.CLEAR_LATENCY_DELAY.value,
                parameters={},
                hypothesis=analysis.hypothesis or (
                    f"Latency SLA violated: average {report.latency.avg_latency_ms}ms "
                    f"exceeds threshold of {report.latency.threshold_ms}ms."
                ),
                rationale=(
                    "Diagnostic Analyst confirmed latency_sla_violation overhead. "
                    "Clearing simulated latency delay restores healthy throughput."
                ),
                supporting_evidence=analysis.evidence_summary or ["high_latency", "latency_violation", "timeout"],
                confidence_score=0.90,
                source="DETERMINISTIC_FALLBACK",
                generated_at=now,
            )

        # Rule 4: Service Unhealthy but specific cause not yet isolated
        if analysis.failure_mode == "unknown_anomaly" or not report.service_health.is_healthy:
            return PlannerRecommendation(
                decision_type=PlannerDecisionType.INVESTIGATE,
                diagnostic_tool=DiagnosticToolName.CHECK_DATABASE_STATUS,
                recovery_action=None,
                parameters={},
                hypothesis=analysis.hypothesis or "Service health degraded/down, but root cause requires deeper investigation.",
                rationale="Service reported unhealthy. Probing database reachability to inspect socket connectivity.",
                supporting_evidence=analysis.evidence_summary or ["service_degraded"],
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
            hypothesis=analysis.hypothesis or "All diagnostic probes confirm the clinic service is fully operational.",
            rationale="Service health, database, configuration, and latency all satisfy healthy baselines.",
            supporting_evidence=analysis.evidence_summary or ["healthy_baseline"],
            confidence_score=1.0,
            source="DETERMINISTIC_FALLBACK",
            generated_at=now,
        )


# Global singleton fallback planner
fallback_planner = DeterministicFallbackPlanner()
