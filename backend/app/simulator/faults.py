"""
In-memory Fault Manager for the simulated clinic.

Controls injecting and resetting operational failure modes cleanly
without modifying anything outside the simulator.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from .config import ClinicConfig, active_config, reset_active_config
from .models import FaultStatusResponse, FaultType

logger = logging.getLogger("civicshield.simulator.faults")


class FaultManager:
    """
    Manages active operational fault injections for the clinic simulator.
    """

    def __init__(self) -> None:
        self.active_faults: set[FaultType] = set()
        self.fault_details: dict[FaultType, dict[str, Any]] = {}

    def inject(self, fault_type: FaultType, params: dict[str, Any] | None = None) -> None:
        """Inject a fault scenario into the simulator."""
        params = params or {}
        self.active_faults.add(fault_type)
        self.fault_details[fault_type] = params

        # Apply fault consequences to simulator runtime state
        if fault_type == FaultType.INVALID_DB_CONFIG:
            # Corrupt the active configuration
            bad_host = params.get("corrupt_host", "corrupt-db-host.internal")
            bad_port = params.get("corrupt_port", 9999)
            active_config.db_host = bad_host
            active_config.db_port = bad_port
            logger.warning("Injected fault: INVALID_DB_CONFIG (host=%s, port=%s)", bad_host, bad_port)

        elif fault_type == FaultType.DB_UNAVAILABLE:
            logger.warning("Injected fault: DB_UNAVAILABLE (simulated network unreachable)")

        elif fault_type == FaultType.HIGH_LATENCY:
            added_ms = params.get("added_latency_ms", 2500)
            self.fault_details[fault_type]["added_latency_ms"] = added_ms
            logger.warning("Injected fault: HIGH_LATENCY (+%d ms)", added_ms)

    def reset(self) -> None:
        """Reset all active faults and return to golden baseline state."""
        self.active_faults.clear()
        self.fault_details.clear()
        reset_active_config()
        logger.info("Fault manager reset: all faults cleared, baseline configuration restored")

    def is_active(self, fault_type: FaultType) -> bool:
        """Check if a specific fault type is currently active."""
        return fault_type in self.active_faults

    def get_latency_overhead_ms(self) -> int:
        """Return added latency in ms if high_latency is injected, otherwise 0."""
        if FaultType.HIGH_LATENCY in self.active_faults:
            return self.fault_details[FaultType.HIGH_LATENCY].get("added_latency_ms", 2500)
        return 0

    def get_status(self) -> FaultStatusResponse:
        """Return current status of all faults."""
        return FaultStatusResponse(
            active_faults=list(self.active_faults),
            details={f.value: d for f, d in self.fault_details.items()},
            timestamp=datetime.now(timezone.utc),
        )


# Global singleton instance
fault_manager = FaultManager()

