from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import date
# Ideally we would import Enums from src.models.trial_models to validate input values,
# but for simplicity we keep strings in Pydantic models here.

router = APIRouter()

# Pydantic Models

class TrialCreate(BaseModel):
    trial_id_nct: str
    title: str
    phase: str
    therapeutic_area: Optional[str] = None
    sponsor_id: Optional[str] = None
    principal_investigator: Optional[str] = None
    target_enrollment: Optional[int] = None
    status: str
    start_date: Optional[date] = None

class TrialResponse(TrialCreate):
    id: int

class ParticipantEnrollment(BaseModel):
    trial_id: int
    subject_number: str
    demographics: Dict
    eligibility_criteria_met: bool
    consent_date: date

class ParticipantResponse(ParticipantEnrollment):
    id: int
    randomization_group: Optional[str] = None
    status: str

class AdverseEventReport(BaseModel):
    participant_id: int
    trial_id: int
    event_description: str
    severity: str
    seriousness: str
    causality: str
    onset_date: date
    reported_to_fda: bool = False

class AdverseEventResponse(AdverseEventReport):
    id: int
    resolution_date: Optional[date] = None

class RandomizationAssignment(BaseModel):
    participant_id: int
    trial_id: int

class RandomizationResponse(BaseModel):
    participant_id: int
    group: str

# Endpoints

@router.get("/trials", response_model=List[TrialResponse])
def get_trials(
    phase: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    # Dummy implementation
    return []

@router.get("/trials/{id}/enrollment-progress")
def get_enrollment_progress(id: int):
    return {"trial_id": id, "enrolled": 0, "target": 100, "percentage": 0.0}

@router.post("/participants/enroll", response_model=ParticipantResponse)
def enroll_participant(participant: ParticipantEnrollment):
    return {
        "id": 1,
        **participant.model_dump(),
        "status": "enrolled",
        "randomization_group": None
    }

@router.get("/participants/{trial_id}/list", response_model=List[ParticipantResponse])
def list_participants(trial_id: int):
    return []

@router.post("/adverse-events/report", response_model=AdverseEventResponse)
def report_adverse_event(event: AdverseEventReport):
    return {
        "id": 1,
        **event.model_dump(),
        "resolution_date": None
    }

@router.get("/adverse-events/{trial_id}/summary")
def get_adverse_events_summary(trial_id: int):
    return {"trial_id": trial_id, "total_events": 0, "serious_events": 0}

@router.get("/analytics/site-performance")
def get_site_performance():
    return {"site_id": "001", "recruitment_rate": "5/month"}

@router.get("/data/export/{trial_id}")
def export_trial_data(trial_id: int):
    return {"trial_id": trial_id, "export_url": "http://example.com/export.csv"}

@router.post("/randomization/assign", response_model=RandomizationResponse)
def assign_randomization(assignment: RandomizationAssignment):
    return {"participant_id": assignment.participant_id, "group": "treatment"}
