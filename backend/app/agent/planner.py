"""
LLM Investigator and Repair Planner.

Interfaces with Google Gemini via langchain-google-genai to analyze diagnostic
evidence and produce typed PlannerRecommendations. Gracefully handles missing keys,
timeouts, and model failures by falling back to the DeterministicFallbackPlanner.
"""

from datetime import datetime, timezone
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from app.diagnostics.models import DiagnosticReport
from app.diagnostics.tools import run_all_diagnostics
from app.recovery.models import ALLOWED_RECOVERY_ACTIONS

from .fallback import fallback_planner
from .models import (
    AgentStatusResponse,
    DiagnosticToolName,
    PlannerRecommendation,
)
from .prompts import HUMAN_PROMPT_TEMPLATE, SYSTEM_PROMPT

logger = logging.getLogger("civicshield.agent.planner")

# Ensure .env is loaded from workspace root or backend directory
env_path_root = Path(__file__).resolve().parents[3] / ".env"
env_path_backend = Path(__file__).resolve().parents[2] / ".env"

if env_path_root.exists():
    load_dotenv(env_path_root)
elif env_path_backend.exists():
    load_dotenv(env_path_backend)
else:
    load_dotenv()


class InvestigationPlanner:
    """
    Hybrid Agentic Planner.
    Attempts live Gemini analysis when configured; automatically falls back
    to deterministic rules if the API key is missing or an error occurs.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash") -> None:
        self.model_name = model_name

    def get_api_key(self) -> str | None:
        """Retrieve Gemini API key from environment, filtering out dummy template values."""
        key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not key or key == "your-api-key-here" or "your-api-key" in key:
            return None
        return key

    def is_model_available(self) -> bool:
        """Check if a valid Gemini API key is configured."""
        return self.get_api_key() is not None

    def plan(
        self,
        report: DiagnosticReport | None = None,
        force_fallback: bool = False,
    ) -> PlannerRecommendation:
        """
        Analyze current diagnostic evidence and generate a recommendation.
        If live model is unavailable or force_fallback is True, uses deterministic fallback.
        """
        if report is None:
            report = run_all_diagnostics()

        api_key = self.get_api_key()

        # Route to Fallback if no valid key is present or forced
        if force_fallback or not api_key:
            logger.info("Engaging deterministic fallback planner (force_fallback=%s, has_key=%s)", force_fallback, bool(api_key))
            return fallback_planner.plan(report)

        # Attempt live Gemini model call
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=api_key,
                temperature=0.0,
                max_retries=1,
                timeout=15,
            )

            structured_llm = llm.with_structured_output(PlannerRecommendation)

            summary_text = report.model_dump_json(indent=2)
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=HUMAN_PROMPT_TEMPLATE.format(diagnostic_summary=summary_text)),
            ]

            logger.info("Invoking Gemini model '%s' for diagnostic analysis...", self.model_name)
            result: PlannerRecommendation = structured_llm.invoke(messages)

            # Ensure metadata fields are cleanly populated
            result.source = "GEMINI_MODEL"
            result.generated_at = datetime.now(timezone.utc)

            logger.info(
                "Gemini recommendation received: %s (action=%s, tool=%s, confidence=%.2f)",
                result.decision_type.value,
                result.recovery_action,
                result.diagnostic_tool.value if result.diagnostic_tool else None,
                result.confidence_score,
            )
            return result

        except Exception as e:
            logger.warning(
                "Gemini model invocation failed (%s). Engaging deterministic fallback planner. Error: %s",
                type(e).__name__,
                str(e),
            )
            fallback_rec = fallback_planner.plan(report)
            fallback_rec.source = f"DETERMINISTIC_FALLBACK ({type(e).__name__})"
            fallback_rec.rationale += (
                f" [Note: Live model call failed ({type(e).__name__}); deterministic fallback engaged.]"
            )
            return fallback_rec

    def get_status(self) -> AgentStatusResponse:
        """Return runtime status of the planner and available capabilities."""
        has_key = self.is_model_available()
        return AgentStatusResponse(
            has_api_key=has_key,
            model_name=self.model_name,
            active_mode="LLM_ONLINE" if has_key else "DETERMINISTIC_FALLBACK",
            available_diagnostic_tools=[t.value for t in DiagnosticToolName],
            allowed_recovery_actions=sorted(ALLOWED_RECOVERY_ACTIONS),
        )


# Global singleton planner instance
investigation_planner = InvestigationPlanner()

