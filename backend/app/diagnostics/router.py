"""
Router exposing diagnostic tools as queryable REST endpoints.
"""

from fastapi import APIRouter, Query

from .models import (
    ConfigEvidence,
    DatabaseEvidence,
    DiagnosticReport,
    LatencyEvidence,
    LogEvidence,
    ServiceHealthEvidence,
)
from .tools import (
    check_database_status,
    check_service_health,
    compare_configuration,
    get_recent_logs,
    measure_latency,
    run_all_diagnostics,
)

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


@router.get("/health", response_model=ServiceHealthEvidence)
def diagnostic_service_health():
    """Run Service Health diagnostic."""
    return check_service_health()


@router.get("/logs", response_model=LogEvidence)
def diagnostic_recent_logs(limit: int = Query(default=15, ge=1, le=100)):
    """Run Recent Logs diagnostic."""
    return get_recent_logs(limit=limit)


@router.get("/database", response_model=DatabaseEvidence)
def diagnostic_database():
    """Run Database Socket & Reachability diagnostic."""
    return check_database_status()


@router.get("/config", response_model=ConfigEvidence)
def diagnostic_config():
    """Run Configuration Comparison diagnostic."""
    return compare_configuration()


@router.get("/latency", response_model=LatencyEvidence)
def diagnostic_latency(samples: int = Query(default=3, ge=1, le=10)):
    """Run Latency & SLA diagnostic."""
    return measure_latency(samples=samples)


@router.get("/report", response_model=DiagnosticReport)
def diagnostic_full_report():
    """Run all diagnostics and consolidate evidence into a single report."""
    return run_all_diagnostics()

