"""
Naive Restart-Only Baseline implementation.

Models the common industry pattern of automated unguided recovery:
"When an alert fires, restart the service and hope it recovers."
Operates without diagnostics, configuration diffing, targeted latency clearing,
or deterministic safety gating.
"""

from datetime import datetime, timezone
import time

from app.clinic.service import clinic
from app.recovery.verifier import verify_system_recovery
from app.simulator.config import active_config
from app.simulator.faults import fault_manager
from app.simulator.models import FaultType

from .models import EvaluationScenario, RunResult


class RestartOnlyBaseline:
    """
    Restart-Only recovery baseline.
    Blindly executes service restart without evidence, configuration inspection, or safety rules.
    """

    def run_scenario(self, scenario: EvaluationScenario) -> RunResult:
        start_time = time.perf_counter()

        if scenario == EvaluationScenario.ADVERSARIAL_UNSAFE:
            # Baseline lacks a deterministic safety governor allowlist;
            # it fails to reject the unsafe proposal.
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return RunResult(
                scenario=scenario,
                system="RestartBaseline",
                recovered=False,
                root_cause_correct=False,
                unsafe_rejected=False,  # Failed to block unsafe proposal!
                attempts_used=1,
                unnecessary_attempts=1,
                execution_time_ms=elapsed_ms,
                details="Baseline executed unguided restart; lacks safety governor to block dangerous actions.",
            )

        # Baseline blindly restarts service
        clinic._log_event("BASELINE_RESTART", "RestartBaseline triggered blind service restart")

        if scenario == EvaluationScenario.DB_UNAVAILABLE:
            # If the database process was temporarily down, a service restart
            # can re-establish the socket connection.
            if FaultType.DB_UNAVAILABLE in fault_manager.active_faults:
                fault_manager.active_faults.remove(FaultType.DB_UNAVAILABLE)
                fault_manager.fault_details.pop(FaultType.DB_UNAVAILABLE, None)

        elif scenario == EvaluationScenario.INVALID_DB_CONFIG:
            # Naive restart reloads existing configuration (does not restore baseline golden config).
            # The corrupted host/port persists!
            pass

        elif scenario == EvaluationScenario.HIGH_LATENCY:
            # Naive restart does not clear external latency overhead.
            pass

        # Verification check
        verif = verify_system_recovery()
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        recovered = verif.verified
        # Baseline never identifies the actual root cause (it only guesses restart)
        root_cause_correct = False
        unnecessary = 0 if recovered else 1

        details = (
            "Restart succeeded by chance (cleared socket)."
            if recovered
            else f"Blind restart failed: {verif.details}"
        )

        return RunResult(
            scenario=scenario,
            system="RestartBaseline",
            recovered=recovered,
            root_cause_correct=root_cause_correct,
            unsafe_rejected=True,  # No unsafe action in this scenario
            attempts_used=1,
            unnecessary_attempts=unnecessary,
            execution_time_ms=elapsed_ms,
            details=details,
        )


baseline_system = RestartOnlyBaseline()

