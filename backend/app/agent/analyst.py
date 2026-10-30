"""
Diagnostic Analyst Agent.

Analyzes raw diagnostic telemetry (health probes, socket reachability,
configuration divergence, latency measurements, logs) and produces a
structured DiagnosticAnalysis identifying suspected component, failure mode,
and evidence-grounded hypothesis.
"""

from datetime import datetime, timezone
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from app.diagnostics.models import DiagnosticReport
from app.diagnostics.tools import run_all_diagnostics

from .models import DiagnosticAnalysis
from .prompts import ANALYST_HUMAN_PROMPT_TEMPLATE, ANALYST_SYSTEM_PROMPT

logger = logging.getLogger("civicshield.agent.analyst")

# Ensure .env is loaded
env_path_root = Path(__file__).resolve().parents[3] / ".env"
env_path_backend = Path(__file__).resolve().parents[2] / ".env"

if env_path_root.exists():
    load_dotenv(env_path_root)
elif env_path_backend.exists():
    load_dotenv(env_path_backend)
else:
    load_dotenv()


class DiagnosticAnalyst:
    """
    Dedicated Diagnostic Analyst Agent.
    Interprets telemetry and establishes root-cause findings before planning recovery.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash") -> None:
        self.model_name = model_name

    def get_api_key(self) -> str | None:
        """Retrieve Gemini API key from environment, filtering out dummy values."""
        key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not key or key == "your-api-key-here" or "your-api-key" in key:
            return None
        return key

    def is_model_available(self) -> bool:
        """Check if a valid Gemini API key is present."""
        return self.get_api_key() is not None

    def analyze(
        self,
        report: DiagnosticReport | None = None,
        force_fallback: bool = False,
    ) -> DiagnosticAnalysis:
        """
        Analyze current diagnostic telemetry and generate a structured diagnosis.
        Falls back cleanly to deterministic rules if offline or key is missing.
        """
        if report is None:
            report = run_all_diagnostics()

        api_key = self.get_api_key()

        # If fallback is forced or no key is present, use deterministic analysis
        if force_fallback or not api_key:
            logger.info("Diagnostic Analyst running in deterministic mode (force_fallback=%s, has_key=%s)", force_fallback, bool(api_key))
            return self._deterministic_analysis(report)

        # Attempt live LLM analysis
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=api_key,
                temperature=0.0,
                max_retries=1,
                timeout=15,
            )
            structured_llm = llm.with_structured_output(DiagnosticAnalysis)

            summary_text = report.model_dump_json(indent=2)
            messages = [
                SystemMessage(content=ANALYST_SYSTEM_PROMPT),
                HumanMessage(content=ANALYST_HUMAN_PROMPT_TEMPLATE.format(diagnostic_summary=summary_text)),
            ]

            logger.info("Diagnostic Analyst querying Gemini model '%s'...", self.model_name)
            analysis: DiagnosticAnalysis = structured_llm.invoke(messages)
            analysis.source = "GEMINI_MODEL"
            analysis.analyzed_at = datetime.now(timezone.utc)

            logger.info(
                "Diagnostic Analyst diagnosis complete: component=%s, failure_mode=%s, confidence=%.2f",
                analysis.suspected_component,
                analysis.failure_mode,
                analysis.confidence_score,
            )
            return analysis

        except Exception as e:
            logger.warning(
                "Diagnostic Analyst live LLM call failed (%s: %s). Falling back to deterministic diagnosis.",
                type(e).__name__,
                str(e),
            )
            fallback = self._deterministic_analysis(report)
            fallback.source = f"DETERMINISTIC_FALLBACK ({type(e).__name__})"
            return fallback

    def _deterministic_analysis(self, report: DiagnosticReport) -> DiagnosticAnalysis:
        """Deterministic rule engine for root-cause diagnosis."""
        now = datetime.now(timezone.utc)

        # Check for simulated unsafe proposal
        from app.simulator.faults import fault_manager
        from app.simulator.models import FaultType

        if fault_manager.is_active(FaultType.UNSAFE_PROPOSAL_SIM):
            return DiagnosticAnalysis(
                suspected_component="database_security",
                failure_mode="adversarial_injection",
                severity="CRITICAL",
                hypothesis="Simulated adversarial fault active: untrusted entity proposing destructive schema modifications.",
                evidence_summary=["simulated_adversarial_event", "security_anomaly"],
                confidence_score=0.99,
                recommend_recovery=True,
                source="DETERMINISTIC_FALLBACK",
                analyzed_at=now,
            )

        # Check configuration drift
        if report.configuration.has_divergence:
            keys_str = ", ".join(report.configuration.divergent_keys)
            return DiagnosticAnalysis(
                suspected_component="configuration",
                failure_mode="invalid_host_config",
                severity="HIGH",
                hypothesis=f"Configuration divergence detected on keys: {keys_str}. Service pointing to invalid backend.",
                evidence_summary=["config_divergence", "unknown_host", *report.configuration.divergent_keys],
                confidence_score=0.95,
                recommend_recovery=True,
                source="DETERMINISTIC_FALLBACK",
                analyzed_at=now,
            )

        # Check database reachability
        if not report.database.is_reachable:
            return DiagnosticAnalysis(
                suspected_component="database",
                failure_mode="db_connection_refused",
                severity="CRITICAL",
                hypothesis="Database server connection refused on port 5432; socket unreachable.",
                evidence_summary=["db_unavailable", "connection_refused", "database_socket_down"],
                confidence_score=0.95,
                recommend_recovery=True,
                source="DETERMINISTIC_FALLBACK",
                analyzed_at=now,
            )

        # Check latency SLA
        if report.latency.sla_violated:
            return DiagnosticAnalysis(
                suspected_component="network",
                failure_mode="latency_sla_violation",
                severity="MEDIUM",
                hypothesis=f"Latency SLA breached: average {report.latency.avg_latency_ms}ms exceeds threshold of {report.latency.threshold_ms}ms.",
                evidence_summary=["high_latency", "sla_breach", f"{report.latency.avg_latency_ms}ms"],
                confidence_score=0.90,
                recommend_recovery=True,
                source="DETERMINISTIC_FALLBACK",
                analyzed_at=now,
            )

        # Check general service health degradation
        if not report.service_health.is_healthy:
            return DiagnosticAnalysis(
                suspected_component="service_core",
                failure_mode="unknown_anomaly",
                severity="HIGH",
                hypothesis="Clinic core service reporting unhealthy/degraded without isolated root cause.",
                evidence_summary=["service_unhealthy", f"status_{report.service_health.status}"],
                confidence_score=0.70,
                recommend_recovery=False,
                source="DETERMINISTIC_FALLBACK",
                analyzed_at=now,
            )

        # Baseline healthy
        return DiagnosticAnalysis(
            suspected_component="healthy",
            failure_mode="healthy",
            severity="LOW",
            hypothesis="All diagnostic probes confirm the clinic service is operating within nominal parameters.",
            evidence_summary=["healthy_baseline", "db_connected", "config_nominal", "latency_within_sla"],
            confidence_score=1.0,
            recommend_recovery=False,
            source="DETERMINISTIC_FALLBACK",
            analyzed_at=now,
        )


diagnostic_analyst = DiagnosticAnalyst()

