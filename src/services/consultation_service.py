from typing import List
from pydantic import BaseModel
from src.models.telemedicine_models import Doctor

class VideoCallConfig(BaseModel):
    consultation_id: int
    room_url: str
    token: str

class ClinicalNotes(BaseModel):
    consultation_id: int
    notes: str
    summary: str

async def match_doctor(patient_id: int, specialty: str, urgency: str) -> List[Doctor]:
    """
    Matches a patient with suitable doctors based on specialty and urgency.
    """
    # Mock implementation: return an empty list or some dummy data if possible
    # For now, returning empty list as we don't have a DB session here
    return []

async def start_video_call(consultation_id: int) -> VideoCallConfig:
    """
    Initiates a video call session for a consultation.
    """
    return VideoCallConfig(
        consultation_id=consultation_id,
        room_url=f"https://telemed.example.com/room/{consultation_id}",
        token="mock-secure-token"
    )

async def generate_clinical_notes(consultation_id: int) -> ClinicalNotes:
    """
    Generates clinical notes for a completed consultation.
    """
    return ClinicalNotes(
        consultation_id=consultation_id,
        notes="Patient complained of mild headache. Recommended rest and hydration.",
        summary="Mild Tension Headache"
    )
