"""
Tests for the simulated clinic service (Phase 2).

Each test function gets a fresh ClinicService via the clinic_app fixture
so tests don't interfere with each other. We test:
  - clinic health endpoint in healthy state
  - listing seed appointments
  - successful booking flow
  - booking validation (bad doctor, bad patient, double-booking)
  - doctor and patient list endpoints
"""

import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def clinic_app():
    """
    Create a fresh FastAPI app with a reset clinic for each test.

    We reload the service module so the singleton ClinicService
    is re-created from seed data every time. This guarantees test
    isolation — no leftover state from a previous test.
    """
    import app.clinic.service as svc_module

    importlib.reload(svc_module)

    from app.clinic.router import router
    from app.clinic.service import clinic  # noqa: F811 — fresh import

    # Patch the router's reference to point at the fresh clinic
    import app.clinic.router as router_module

    router_module.clinic = clinic

    test_app = FastAPI()
    test_app.include_router(router)
    return TestClient(test_app)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


def test_clinic_health_returns_healthy(clinic_app):
    resp = clinic_app.get("/clinic/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["active_doctors"] == 4
    assert data["pending_appointments"] == 2  # 2 scheduled in seed data
    assert "timestamp" in data


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------


def test_list_seed_appointments(clinic_app):
    resp = clinic_app.get("/clinic/appointments")
    assert resp.status_code == 200
    appts = resp.json()
    assert len(appts) == 3  # 3 seed appointments
    ids = {a["id"] for a in appts}
    assert ids == {"A-0001", "A-0002", "A-0003"}


# ---------------------------------------------------------------------------
# Booking — happy path
# ---------------------------------------------------------------------------


def test_book_appointment_success(clinic_app):
    """Book a new appointment with valid data and verify it appears."""
    payload = {
        "patient_id": "P-1004",
        "doctor_id": "D-101",
        "date": "2025-03-17",
        "time": "11:00",
        "reason": "Follow-up blood pressure check",
    }
    resp = clinic_app.post("/clinic/book", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["success"] is True
    assert data["appointment"]["patient_id"] == "P-1004"
    assert data["appointment"]["doctor_id"] == "D-101"
    assert data["appointment"]["status"] == "scheduled"
    assert "A-" in data["appointment"]["id"]

    # Verify it now appears in the list
    appts = clinic_app.get("/clinic/appointments").json()
    new_ids = {a["id"] for a in appts}
    assert data["appointment"]["id"] in new_ids


# ---------------------------------------------------------------------------
# Booking — validation failures
# ---------------------------------------------------------------------------


def test_book_unknown_doctor(clinic_app):
    payload = {
        "patient_id": "P-1001",
        "doctor_id": "D-999",
        "date": "2025-03-17",
        "time": "09:00",
        "reason": "Test",
    }
    resp = clinic_app.post("/clinic/book", json=payload)
    data = resp.json()
    assert data["success"] is False
    assert "not found" in data["message"]


def test_book_unknown_patient(clinic_app):
    payload = {
        "patient_id": "P-9999",
        "doctor_id": "D-101",
        "date": "2025-03-17",
        "time": "09:00",
        "reason": "Test",
    }
    resp = clinic_app.post("/clinic/book", json=payload)
    data = resp.json()
    assert data["success"] is False
    assert "not found" in data["message"]


def test_double_booking_rejected(clinic_app):
    """The seed data has D-101 at 2025-03-15 10:30 — booking that slot again must fail."""
    payload = {
        "patient_id": "P-1004",
        "doctor_id": "D-101",
        "date": "2025-03-15",
        "time": "10:30",
        "reason": "Conflicting slot",
    }
    resp = clinic_app.post("/clinic/book", json=payload)
    data = resp.json()
    assert data["success"] is False
    assert "already has an appointment" in data["message"]


# ---------------------------------------------------------------------------
# Rosters
# ---------------------------------------------------------------------------


def test_list_doctors(clinic_app):
    resp = clinic_app.get("/clinic/doctors")
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 4
    names = {d["name"] for d in docs}
    assert "Dr. Ada Sharma" in names
    assert "Dr. Viktor Frankenstien" in names


def test_list_patients(clinic_app):
    resp = clinic_app.get("/clinic/patients")
    assert resp.status_code == 200
    patients = resp.json()
    assert len(patients) == 4


# ---------------------------------------------------------------------------
# Event log
# ---------------------------------------------------------------------------


def test_event_log_has_startup(clinic_app):
    resp = clinic_app.get("/clinic/logs")
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) >= 1
    assert logs[0]["event"] == "SERVICE_START"

