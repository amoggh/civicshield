"""
Clinic service layer — business logic and in-memory state.

This module owns the single source of truth for the simulated clinic:
its current status, doctor roster, patient list, and appointment book.

Phase 3 will add fault injection by flipping the service state to
DEGRADED or DOWN. For now everything starts healthy.
"""

import logging
from datetime import datetime, timezone

from app.simulator.config import active_config
from app.simulator.faults import fault_manager
from app.simulator.models import FaultType

from .data import DOCTORS, PATIENTS, SEED_APPOINTMENTS
from .models import (
    Appointment,
    AppointmentStatus,
    BookingRequest,
    BookingResponse,
    ClinicHealthResponse,
    Doctor,
    Patient,
    ServiceStatus,
)

logger = logging.getLogger("civicshield.clinic")


class ClinicService:
    """
    In-memory simulated clinic.

    All state lives in Python lists/dicts — no database. Restarting
    the server resets everything to the seed data.
    """

    def __init__(self) -> None:
        self.status: ServiceStatus = ServiceStatus.HEALTHY
        self.doctors: list[Doctor] = [d.model_copy() for d in DOCTORS]
        self.patients: list[Patient] = [p.model_copy() for p in PATIENTS]
        self.appointments: list[Appointment] = [
            a.model_copy() for a in SEED_APPOINTMENTS
        ]
        self._next_appointment_id = len(self.appointments) + 1
        # Structured log of every significant event (for the dashboard later)
        self.event_log: list[dict] = []
        self._log_event("SERVICE_START", "Clinic service initialised in HEALTHY state")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _log_event(self, event_type: str, detail: str) -> dict:
        """Append a structured event and also emit a Python log line."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "detail": detail,
            "service_status": self.status.value,
        }
        self.event_log.append(entry)
        logger.info("%s | %s | %s", event_type, detail, self.status.value)
        return entry

    def _find_doctor(self, doctor_id: str) -> Doctor | None:
        return next((d for d in self.doctors if d.id == doctor_id), None)

    def _find_patient(self, patient_id: str) -> Patient | None:
        return next((p for p in self.patients if p.id == patient_id), None)

    # ------------------------------------------------------------------
    # Public API (called by the router)
    # ------------------------------------------------------------------

    @property
    def current_status(self) -> ServiceStatus:
        """Resolve current status taking active faults into account."""
        if fault_manager.is_active(FaultType.DB_UNAVAILABLE):
            return ServiceStatus.DOWN
        if fault_manager.is_active(FaultType.INVALID_DB_CONFIG):
            return ServiceStatus.DEGRADED
        if fault_manager.is_active(FaultType.HIGH_LATENCY):
            return ServiceStatus.DEGRADED
        return self.status

    def get_health(self) -> ClinicHealthResponse:
        """Return the current health status of the clinic service."""
        effective_status = self.current_status
        pending = sum(
            1 for a in self.appointments
            if a.status == AppointmentStatus.SCHEDULED
        )
        return ClinicHealthResponse(
            status=effective_status,
            message=self._health_message(effective_status),
            active_doctors=sum(1 for d in self.doctors if d.available),
            pending_appointments=pending,
            timestamp=datetime.now(timezone.utc),
        )

    def list_appointments(self) -> list[Appointment]:
        """Return all appointments (any status)."""
        if self.current_status == ServiceStatus.DOWN:
            self._log_event("ACCESS_DENIED", "Appointment list requested while service is DOWN")
            return []
        return list(self.appointments)

    def list_doctors(self) -> list[Doctor]:
        """Return the doctor roster."""
        return list(self.doctors)

    def list_patients(self) -> list[Patient]:
        """Return the patient roster."""
        return list(self.patients)

    def book_appointment(self, req: BookingRequest) -> BookingResponse:
        """
        Try to book a new appointment. Validates inputs against the
        in-memory roster and returns success/failure.
        """
        effective_status = self.current_status

        # Gate: check active faults
        if fault_manager.is_active(FaultType.DB_UNAVAILABLE):
            self._log_event("DB_CONNECTION_REFUSED", "Database connection refused on 127.0.0.1:5432")
            return BookingResponse(
                success=False,
                message="Cannot book: Database unavailable (connection refused)",
            )

        if fault_manager.is_active(FaultType.INVALID_DB_CONFIG):
            self._log_event(
                "CONFIG_ERROR",
                f"Failed connecting to database at {active_config.db_host}:{active_config.db_port}",
            )
            return BookingResponse(
                success=False,
                message=f"Cannot book: Database host unreachable ({active_config.db_host}:{active_config.db_port})",
            )

        # Gate: service must be healthy to accept new bookings
        if effective_status != ServiceStatus.HEALTHY:
            self._log_event(
                "BOOKING_REJECTED",
                f"Booking rejected — service is {effective_status.value}",
            )
            return BookingResponse(
                success=False,
                message=f"Cannot book: service is {effective_status.value}",
            )

        # Validate doctor exists and is available
        doctor = self._find_doctor(req.doctor_id)
        if doctor is None:
            return BookingResponse(
                success=False,
                message=f"Doctor '{req.doctor_id}' not found",
            )
        if not doctor.available:
            return BookingResponse(
                success=False,
                message=f"Doctor '{doctor.name}' is not available",
            )

        # Validate patient exists
        if self._find_patient(req.patient_id) is None:
            return BookingResponse(
                success=False,
                message=f"Patient '{req.patient_id}' not found",
            )

        # Check for double-booking (same doctor, date, time)
        for appt in self.appointments:
            if (
                appt.doctor_id == req.doctor_id
                and appt.date == req.date
                and appt.time == req.time
                and appt.status == AppointmentStatus.SCHEDULED
            ):
                return BookingResponse(
                    success=False,
                    message=(
                        f"Doctor '{doctor.name}' already has an appointment "
                        f"at {req.date} {req.time}"
                    ),
                )

        # All checks passed — create the appointment
        appt_id = f"A-{self._next_appointment_id:04d}"
        self._next_appointment_id += 1

        new_appt = Appointment(
            id=appt_id,
            patient_id=req.patient_id,
            doctor_id=req.doctor_id,
            date=req.date,
            time=req.time,
            reason=req.reason,
        )
        self.appointments.append(new_appt)

        self._log_event(
            "BOOKING_CREATED",
            f"Appointment {appt_id}: {req.patient_id} with {req.doctor_id} "
            f"on {req.date} at {req.time}",
        )

        return BookingResponse(
            success=True,
            appointment=new_appt,
            message=f"Appointment {appt_id} booked successfully",
        )

    def get_event_log(self) -> list[dict]:
        """Return the full structured event log."""
        return list(self.event_log)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _health_message(self, status: ServiceStatus | None = None) -> str:
        s = status or self.status
        messages = {
            ServiceStatus.HEALTHY: "All systems operational",
            ServiceStatus.DEGRADED: "Service is experiencing issues",
            ServiceStatus.DOWN: "Service is unavailable",
        }
        return messages.get(s, "Unknown status")


# ---------------------------------------------------------------------------
# Module-level singleton so the whole app shares one clinic instance.
# This resets on server restart, which is fine for a simulation.
# ---------------------------------------------------------------------------
clinic = ClinicService()

