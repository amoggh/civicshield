"""
Deterministic verification probe for post-recovery validation.

Proves that an applied repair actually solved the underlying incident by
running four distinct operational checks:
1. Service health check
2. Database reachability check
3. Latency SLA check
4. End-to-end synthetic booking test

A repair is NEVER marked successful unless all four verification checks pass.
"""

from datetime import datetime, timezone
import uuid

from app.clinic.models import BookingRequest
from app.clinic.service import clinic
from app.diagnostics.tools import (
    check_database_status,
    check_service_health,
    measure_latency,
)

from .models import VerificationResult


def verify_system_recovery() -> VerificationResult:
    """
    Run the complete post-repair verification suite.
    Returns a structured VerificationResult.
    """
    now = datetime.now(timezone.utc)

    # 1. Health Probe
    health_evidence = check_service_health()
    health_ok = health_evidence.is_healthy and health_evidence.status == "healthy"

    # 2. Database Reachability Probe
    db_evidence = check_database_status()
    db_ok = db_evidence.is_reachable and db_evidence.status_code == "CONNECTED"

    # 3. Latency SLA Probe
    latency_evidence = measure_latency(samples=2)
    latency_ok = not latency_evidence.sla_violated

    # 4. Functional Synthetic Booking Probe
    probe_token = uuid.uuid4().hex
    test_req = BookingRequest(
        patient_id="P-1001",
        doctor_id="D-102",
        date=f"2099-12-{(int(probe_token[:2], 16) % 28) + 1:02d}",
        time=f"{(int(probe_token[2:4], 16) % 24):02d}:{(int(probe_token[4:6], 16) % 60):02d}",
        reason=f"Automated verification probe [{probe_token[:8]}]",
    )
    booking_resp = clinic.book_appointment(test_req)
    booking_test_ok = booking_resp.success

    # Clean up test probe appointment so probe slots never accumulate or collide
    if booking_test_ok and booking_resp.appointment:
        clinic.appointments = [
            a for a in clinic.appointments if a.id != booking_resp.appointment.id
        ]

    # Consolidation
    all_passed = health_ok and db_ok and latency_ok and booking_test_ok

    failures = []
    if not health_ok:
        failures.append(f"Health degraded (status: {health_evidence.status})")
    if not db_ok:
        failures.append(f"Database unreachable ({db_evidence.status_code}: {db_evidence.error_detail})")
    if not latency_ok:
        failures.append(f"Latency SLA violated (avg: {latency_evidence.avg_latency_ms}ms > {latency_evidence.threshold_ms}ms)")
    if not booking_test_ok:
        failures.append(f"Synthetic booking probe failed: {booking_resp.message}")

    if all_passed:
        details = (
            "Verification PASSED: Service is healthy, database is connected, "
            f"latency is normal ({latency_evidence.avg_latency_ms}ms), "
            "and synthetic booking succeeded."
        )
    else:
        details = f"Verification FAILED: {'; '.join(failures)}"

    return VerificationResult(
        verified=all_passed,
        health_ok=health_ok,
        database_ok=db_ok,
        latency_ok=latency_ok,
        booking_test_ok=booking_test_ok,
        details=details,
        timestamp=now,
    )

