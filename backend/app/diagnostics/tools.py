"""
Deterministic diagnostic tools for the clinic incident investigation.

Each function runs a specific diagnostic check, returning structured Pydantic
evidence. These tools will be invoked by the LangChain/LangGraph agent in Phase 4.
"""

from datetime import datetime, timezone

from app.clinic.models import ServiceStatus
from app.clinic.service import clinic
from app.simulator.config import BASELINE_CONFIG, active_config
from app.simulator.faults import fault_manager
from app.simulator.models import FaultType

from .models import (
    ConfigDiffItem,
    ConfigEvidence,
    DatabaseEvidence,
    DiagnosticReport,
    LatencyEvidence,
    LogEntry,
    LogEvidence,
    ServiceHealthEvidence,
)

# Known error event types in clinic structured logs
ERROR_EVENT_TYPES = {
    "CONFIG_ERROR",
    "DB_CONNECTION_REFUSED",
    "DB_UNAVAILABLE",
    "BOOKING_REJECTED",
    "ACCESS_DENIED",
    "LATENCY_SLA_VIOLATION",
}


def check_service_health() -> ServiceHealthEvidence:
    """
    Diagnostic Tool 1: Probe clinic service health.
    Returns status, active doctors, pending appointments, and status message.
    """
    health = clinic.get_health()
    return ServiceHealthEvidence(
        status=health.status.value,
        is_healthy=(health.status == ServiceStatus.HEALTHY),
        active_doctors=health.active_doctors,
        pending_appointments=health.pending_appointments,
        message=health.message,
        observed_at=datetime.now(timezone.utc),
    )


def get_recent_logs(limit: int = 15) -> LogEvidence:
    """
    Diagnostic Tool 2: Retrieve and analyze recent structured event logs.
    Flags errors, connection drops, and rejections.
    """
    raw_logs = clinic.get_event_log()
    selected_logs = raw_logs[-limit:] if len(raw_logs) > limit else raw_logs

    parsed_entries: list[LogEntry] = []
    error_count = 0

    for entry in selected_logs:
        event_name = entry.get("event", "")
        status_val = entry.get("service_status", "")
        is_err = (
            event_name in ERROR_EVENT_TYPES
            or status_val in {"degraded", "down"}
        )
        if is_err:
            error_count += 1

        parsed_entries.append(
            LogEntry(
                timestamp=entry.get("timestamp", ""),
                event=event_name,
                detail=entry.get("detail", ""),
                service_status=status_val,
                is_error=is_err,
            )
        )

    return LogEvidence(
        total_logs=len(raw_logs),
        error_count=error_count,
        has_errors=(error_count > 0),
        recent_entries=parsed_entries,
        observed_at=datetime.now(timezone.utc),
    )


def check_database_status() -> DatabaseEvidence:
    """
    Diagnostic Tool 3: Check database socket reachability and host configuration.
    Identifies connection refusals, invalid host resolutions, and baseline health.
    """
    now = datetime.now(timezone.utc)

    # Check 1: Is the active configuration pointing to an invalid host or port?
    if (
        active_config.db_host != BASELINE_CONFIG.db_host
        or active_config.db_port != BASELINE_CONFIG.db_port
    ):
        return DatabaseEvidence(
            is_reachable=False,
            host=active_config.db_host,
            port=active_config.db_port,
            status_code="UNKNOWN_HOST_OR_PORT",
            error_detail=(
                f"Cannot establish connection to '{active_config.db_host}:{active_config.db_port}'. "
                f"Configured address differs from baseline {BASELINE_CONFIG.db_host}:{BASELINE_CONFIG.db_port}."
            ),
            response_time_ms=0.0,
            observed_at=now,
        )

    # Check 2: Is the simulated database socket down?
    if fault_manager.is_active(FaultType.DB_UNAVAILABLE):
        return DatabaseEvidence(
            is_reachable=False,
            host=active_config.db_host,
            port=active_config.db_port,
            status_code="CONNECTION_REFUSED",
            error_detail="Connection refused by simulated database process on port 5432.",
            response_time_ms=0.0,
            observed_at=now,
        )

    # Healthy state
    return DatabaseEvidence(
        is_reachable=True,
        host=active_config.db_host,
        port=active_config.db_port,
        status_code="CONNECTED",
        error_detail=None,
        response_time_ms=3.5,
        observed_at=now,
    )


def compare_configuration() -> ConfigEvidence:
    """
    Diagnostic Tool 4: Compare active configuration against the known golden baseline.
    Detects configuration drift, corrupted hosts/ports, or modified limits.
    """
    now = datetime.now(timezone.utc)
    baseline_dict = BASELINE_CONFIG.model_dump()
    active_dict = active_config.model_dump()

    diffs: list[ConfigDiffItem] = []
    divergent_keys: list[str] = []

    for key, baseline_val in baseline_dict.items():
        current_val = active_dict.get(key)
        divergent = baseline_val != current_val
        if divergent:
            divergent_keys.append(key)
        diffs.append(
            ConfigDiffItem(
                key=key,
                baseline_value=baseline_val,
                current_value=current_val,
                is_divergent=divergent,
            )
        )

    return ConfigEvidence(
        has_divergence=(len(divergent_keys) > 0),
        divergent_keys=divergent_keys,
        diffs=diffs,
        observed_at=now,
    )


def measure_latency(samples: int = 3) -> LatencyEvidence:
    """
    Diagnostic Tool 5: Measure synthetic round-trip response latency.
    Flags SLA violations when average latency exceeds the configured timeout threshold.
    """
    now = datetime.now(timezone.utc)
    base_latency = 12.0  # nominal healthy latency in ms
    overhead = fault_manager.get_latency_overhead_ms()

    # Create deterministic synthetic sample variations
    sample_latencies: list[float] = [
        round(base_latency + overhead + (i * 4.5), 1)
        for i in range(max(1, samples))
    ]
    avg_latency = round(sum(sample_latencies) / len(sample_latencies), 1)
    threshold = float(active_config.timeout_ms)

    return LatencyEvidence(
        sample_latencies_ms=sample_latencies,
        avg_latency_ms=avg_latency,
        threshold_ms=threshold,
        sla_violated=(avg_latency > threshold),
        observed_at=now,
    )


def run_all_diagnostics() -> DiagnosticReport:
    """Consolidated runner gathering evidence across all diagnostic tools."""
    return DiagnosticReport(
        service_health=check_service_health(),
        database=check_database_status(),
        configuration=compare_configuration(),
        latency=measure_latency(),
        logs=get_recent_logs(),
        generated_at=datetime.now(timezone.utc),
    )

