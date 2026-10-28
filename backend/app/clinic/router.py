"""
FastAPI router for the simulated clinic service.

All endpoints are under the /clinic prefix. The router delegates to the
ClinicService singleton — it doesn't contain business logic itself.
"""

from fastapi import APIRouter

from .models import (
    Appointment,
    BookingRequest,
    BookingResponse,
    ClinicHealthResponse,
    Doctor,
    Patient,
)
from .service import clinic

router = APIRouter(prefix="/clinic", tags=["Clinic"])


@router.get("/health", response_model=ClinicHealthResponse)
def clinic_health():
    """Check the simulated clinic's health status."""
    return clinic.get_health()


@router.get("/appointments", response_model=list[Appointment])
def list_appointments():
    """List all appointments (scheduled, completed, and cancelled)."""
    return clinic.list_appointments()


@router.get("/doctors", response_model=list[Doctor])
def list_doctors():
    """List the doctor roster."""
    return clinic.list_doctors()


@router.get("/patients", response_model=list[Patient])
def list_patients():
    """List the patient roster."""
    return clinic.list_patients()


@router.post("/book", response_model=BookingResponse)
def book_appointment(req: BookingRequest):
    """
    Book a new appointment.

    Validates the patient and doctor exist, checks for double-bookings,
    and rejects requests if the service is not healthy.
    """
    return clinic.book_appointment(req)


@router.get("/logs", response_model=list[dict])
def get_event_log():
    """Return the clinic's structured event log (newest last)."""
    return clinic.get_event_log()

