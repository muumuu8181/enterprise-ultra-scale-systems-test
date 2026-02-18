from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from src.services import consultation_service
from src.models.telemedicine_models import ConsultationType

router = APIRouter()

class ConsultationBookingRequest(BaseModel):
    patient_id: int
    doctor_id: int
    consultation_type: ConsultationType
    scheduled_at: datetime
    chief_complaint: str

class PrescriptionCreateRequest(BaseModel):
    medications: List[Dict[str, Any]]
    dosage_instructions: str
    refills_allowed: int
    pharmacy_id: Optional[int] = None

@router.post("/consultations/book")
async def book_consultation(request: ConsultationBookingRequest):
    # Mock implementation
    return {"status": "booked", "id": 123, "details": request.model_dump()}

@router.get("/consultations/{id}/join-video")
async def join_video_call(id: int):
    config = await consultation_service.start_video_call(id)
    return config

@router.get("/doctors/search")
async def search_doctors(
    specialty: Optional[str] = Query(None),
    language: Optional[str] = Query(None)
):
    # Mock implementation
    # Using match_doctor service as a proxy for search
    doctors = await consultation_service.match_doctor(
        patient_id=0,
        specialty=specialty or "general",
        urgency="routine"
    )
    return doctors

@router.get("/doctors/{id}/availability")
async def get_doctor_availability(id: int):
    # Mock implementation
    return {
        "doctor_id": id,
        "available_slots": [
            {"start": "2023-10-27T09:00:00Z", "end": "2023-10-27T09:30:00Z"},
            {"start": "2023-10-27T10:00:00Z", "end": "2023-10-27T10:30:00Z"}
        ]
    }

@router.post("/consultations/{id}/prescribe")
async def prescribe_medication(id: int, request: PrescriptionCreateRequest):
    # Mock implementation
    return {
        "status": "prescribed",
        "consultation_id": id,
        "prescription_id": 456,
        "details": request.model_dump()
    }

@router.get("/consultations/{id}/notes")
async def get_consultation_notes(id: int):
    notes = await consultation_service.generate_clinical_notes(id)
    return notes
