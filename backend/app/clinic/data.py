"""
Synthetic in-memory data for the simulated clinic.

Every name, ID, and date here is fictional. This data seeds the clinic
when the server starts. It resets on every restart (no persistence needed).
"""

from .models import Appointment, AppointmentStatus, Doctor, Patient

# --- Doctors (all fictional) ---------------------------------------------------

DOCTORS: list[Doctor] = [
    Doctor(id="D-101", name="Dr. Ada Sharma",    specialty="General Practice"),
    Doctor(id="D-102", name="Dr. Ben Okafor",    specialty="Pediatrics"),
    Doctor(id="D-103", name="Dr. Clara Mendes",  specialty="Dermatology"),
    Doctor(id="D-104", name="Dr. Viktor Frankenstien", specialty="Radiology"),
]

# --- Patients (all fictional) --------------------------------------------------

PATIENTS: list[Patient] = [
    Patient(id="P-1001", name="Ravi Patel",      age=34),
    Patient(id="P-1002", name="Lena Johansson",  age=28),
    Patient(id="P-1003", name="Marcus Chen",     age=45),
    Patient(id="P-1004", name="Fatima Al-Rashid", age=62),
]

# --- Pre-existing appointments --------------------------------------------------

SEED_APPOINTMENTS: list[Appointment] = [
    Appointment(
        id="A-0001",
        patient_id="P-1001",
        doctor_id="D-101",
        date="2025-03-15",
        time="10:30",
        reason="Routine checkup",
        status=AppointmentStatus.SCHEDULED,
    ),
    Appointment(
        id="A-0002",
        patient_id="P-1002",
        doctor_id="D-102",
        date="2025-03-15",
        time="14:00",
        reason="Child vaccination follow-up",
        status=AppointmentStatus.SCHEDULED,
    ),
    Appointment(
        id="A-0003",
        patient_id="P-1003",
        doctor_id="D-103",
        date="2025-03-16",
        time="09:00",
        reason="Skin rash consultation",
        status=AppointmentStatus.COMPLETED,
    ),
]

