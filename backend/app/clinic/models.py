"""
Pydantic models for the simulated clinic service.

These define the exact shape of every API request and response.
Using Pydantic means FastAPI will auto-validate inputs and auto-generate
OpenAPI docs at /docs. All data is synthetic — no real patient information.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ServiceStatus(str, Enum):
    """Possible states of the clinic service."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"          # Slow or partially broken
    DOWN = "down"                  # Completely unavailable


class AppointmentStatus(str, Enum):
    """Possible states of a single appointment."""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ClinicHealthResponse(BaseModel):
    """Returned by GET /clinic/health."""
    status: ServiceStatus
    message: str
    active_doctors: int = Field(ge=0)
    pending_appointments: int = Field(ge=0)
    timestamp: datetime


class Doctor(BaseModel):
    id: str
    name: str
    specialty: str
    available: bool = True


class Patient(BaseModel):
    id: str
    name: str
    age: int = Field(ge=0, le=150)


class Appointment(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    date: str                       # ISO date string, e.g. "2025-03-15"
    time: str                       # e.g. "10:30"
    reason: str
    status: AppointmentStatus = AppointmentStatus.SCHEDULED


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class BookingRequest(BaseModel):
    """Body for POST /clinic/book."""
    patient_id: str = Field(min_length=1)
    doctor_id: str = Field(min_length=1)
    date: str = Field(min_length=1)
    time: str = Field(min_length=1)
    reason: str = Field(min_length=1, max_length=200)


class BookingResponse(BaseModel):
    """Returned by POST /clinic/book on success."""
    success: bool
    appointment: Appointment | None = None
    message: str

