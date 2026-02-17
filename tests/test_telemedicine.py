import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.v1.consultations import router
from src.models.telemedicine_models import Doctor, Consultation, Prescription, ConsultationType, ConsultationStatus
from src.services import consultation_service
from datetime import datetime, timezone
import asyncio

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_models_exist():
    # Verify models are importable and have expected attributes
    d = Doctor(id=1, user_id=1, specialty="Test", medical_license="LIC123", consultation_fee=100.0, available_slots=[], languages=[], rating=5.0)
    assert d.specialty == "Test"

    c = Consultation(id=1, patient_id=2, doctor_id=1, consultation_type=ConsultationType.VIDEO, scheduled_at=datetime.now(timezone.utc), status=ConsultationStatus.SCHEDULED, chief_complaint="Test", duration_min=30)
    assert c.status == ConsultationStatus.SCHEDULED

    p = Prescription(id=1, consultation_id=1, medications=[], dosage_instructions="Test", refills_allowed=0, pharmacy_id=1)
    assert p.refills_allowed == 0

def test_enums():
    assert ConsultationType.VIDEO.value == "video"
    assert ConsultationStatus.SCHEDULED.value == "scheduled"

@pytest.mark.asyncio
async def test_service_functions():
    doctors = await consultation_service.match_doctor(1, "cardiology", "high")
    assert isinstance(doctors, list)

    config = await consultation_service.start_video_call(101)
    assert config.consultation_id == 101
    assert "https" in config.room_url

    notes = await consultation_service.generate_clinical_notes(101)
    assert notes.consultation_id == 101
    assert len(notes.notes) > 0

def test_api_endpoints():
    # Test Book Consultation
    response = client.post("/consultations/book", json={
        "patient_id": 1,
        "doctor_id": 2,
        "consultation_type": "video",
        "scheduled_at": "2023-12-01T10:00:00",
        "chief_complaint": "Fever"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "booked"
    assert data["id"] == 123

    # Test Join Video Call
    response = client.get("/consultations/123/join-video")
    assert response.status_code == 200
    data = response.json()
    assert "room_url" in data
    assert data["consultation_id"] == 123

    # Test Search Doctors
    response = client.get("/doctors/search?specialty=cardiology")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Test Doctor Availability
    response = client.get("/doctors/5/availability")
    assert response.status_code == 200
    data = response.json()
    assert "available_slots" in data
    assert data["doctor_id"] == 5

    # Test Prescribe
    response = client.post("/consultations/123/prescribe", json={
        "medications": [{"name": "Aspirin", "dose": "500mg"}],
        "dosage_instructions": "Take one daily",
        "refills_allowed": 1,
        "pharmacy_id": 10
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "prescribed"
    assert data["prescription_id"] == 456

    # Test Notes
    response = client.get("/consultations/123/notes")
    assert response.status_code == 200
    data = response.json()
    assert "notes" in data
    assert data["consultation_id"] == 123
