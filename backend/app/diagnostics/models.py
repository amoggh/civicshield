"""
Structured evidence models returned by deterministic diagnostic tools.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ServiceHealthEvidence(BaseModel):
    """Evidence from checking overall service health."""
    status: str
    is_healthy: bool
    active_doctors: int
    pending_appointments: int
    message: str
    observed_at: datetime


class LogEntry(BaseModel):
    """A single structured log record."""
    timestamp: str
    event: str
    detail: str
    service_status: str
    is_error: bool = False


class LogEvidence(BaseModel):
    """Evidence from analyzing recent service and system event logs."""
    total_logs: int
    error_count: int
    has_errors: bool
    recent_entries: list[LogEntry]
    observed_at: datetime


class DatabaseEvidence(BaseModel):
    """Evidence from probing the database connection and socket."""
    is_reachable: bool
    host: str
    port: int
    status_code: str
    error_detail: str | None = None
    response_time_ms: float
    observed_at: datetime


class ConfigDiffItem(BaseModel):
    """Comparison item for a single configuration key."""
    key: str
    baseline_value: Any
    current_value: Any
    is_divergent: bool


class ConfigEvidence(BaseModel):
    """Evidence from comparing active configuration against the golden baseline."""
    has_divergence: bool
    divergent_keys: list[str]
    diffs: list[ConfigDiffItem]
    observed_at: datetime


class LatencyEvidence(BaseModel):
    """Evidence from synthetic round-trip latency measurements."""
    sample_latencies_ms: list[float]
    avg_latency_ms: float
    threshold_ms: float
    sla_violated: bool
    observed_at: datetime


class DiagnosticReport(BaseModel):
    """Comprehensive snapshot consolidating all 5 diagnostic tools."""
    service_health: ServiceHealthEvidence
    database: DatabaseEvidence
    configuration: ConfigEvidence
    latency: LatencyEvidence
    logs: LogEvidence
    generated_at: datetime

