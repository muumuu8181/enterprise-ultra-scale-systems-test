from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from src.models.transplant_models import OrganType, WaitlistStatus, DonorType, CrossmatchResult, AcceptanceStatus

router = APIRouter()

# --- Pydantic Schemas ---

class WaitlistEntryResponse(BaseModel):
    id: int
    patient_id: str
    organ_needed: OrganType
    blood_type: str
    urgency_score: int
    transplant_center_id: str
    status: WaitlistStatus

class DonorOrganResponse(BaseModel):
    id: int
    donor_id: str
    organ_type: OrganType
    blood_type: str
    condition_score: int
    is_available: bool = True

class CandidateResponse(BaseModel):
    patient_id: str
    compatibility_score: float
    rank: int

class TransportPlanResponse(BaseModel):
    match_id: int
    origin: str
    destination: str
    estimated_arrival: str
    transport_mode: str

class WaitTimeAnalytics(BaseModel):
    organ: OrganType
    average_wait_days: float
    median_wait_days: float

class GraftSurvivalRate(BaseModel):
    organ: OrganType
    one_year_survival_rate: float
    three_year_survival_rate: float
    five_year_survival_rate: float

class RegisterOrganRequest(BaseModel):
    donor_id: str
    donor_type: DonorType
    organ_type: OrganType
    blood_type: str
    hla_typing: Dict[str, Any]
    condition_score: int

class RunMatchingRequest(BaseModel):
    organ_id: int
    algorithm_version: Optional[str] = "v1.0"

class MatchingResponse(BaseModel):
    match_id: int
    recipient_id: str
    score: float
    status: str

# --- Endpoints ---

@router.get("/waitlist", response_model=List[WaitlistEntryResponse])
async def get_waitlist(organ: Optional[OrganType] = None, blood_type: Optional[str] = None):
    """
    Get current waitlist entries, optionally filtered by organ and blood type.
    """
    # Mock data
    return [
        WaitlistEntryResponse(
            id=1,
            patient_id="P12345",
            organ_needed=OrganType.kidney,
            blood_type="O+",
            urgency_score=8,
            transplant_center_id="TC-001",
            status=WaitlistStatus.active
        )
    ]

@router.get("/waitlist/{id}/position")
async def get_waitlist_position(id: int):
    """
    Get the position of a specific patient on the waitlist.
    """
    return {"id": id, "position": 12, "percentile": 85.0}

@router.get("/donors/{id}/available-organs", response_model=List[DonorOrganResponse])
async def get_donor_organs(id: str):
    """
    Get available organs for a registered donor.
    """
    return [
        DonorOrganResponse(
            id=101,
            donor_id=id,
            organ_type=OrganType.liver,
            blood_type="A+",
            condition_score=95
        )
    ]

@router.get("/matching/{organ_id}/candidates", response_model=List[CandidateResponse])
async def get_matching_candidates(organ_id: int):
    """
    Get a ranked list of candidates for a specific donor organ.
    """
    return [
        CandidateResponse(patient_id="P98765", compatibility_score=0.92, rank=1),
        CandidateResponse(patient_id="P12345", compatibility_score=0.88, rank=2),
    ]

@router.get("/logistics/transport-plan/{match_id}", response_model=TransportPlanResponse)
async def get_transport_plan(match_id: int):
    """
    Get the logistics plan for transporting an organ.
    """
    return TransportPlanResponse(
        match_id=match_id,
        origin="General Hospital",
        destination="University Medical Center",
        estimated_arrival="2023-11-15T14:30:00Z",
        transport_mode="Air Ambulance"
    )

@router.get("/analytics/wait-times", response_model=WaitTimeAnalytics)
async def get_wait_times(organ: OrganType = Query(...)):
    """
    Get wait time analytics for a specific organ type.
    """
    return WaitTimeAnalytics(
        organ=organ,
        average_wait_days=345.5,
        median_wait_days=300.0
    )

@router.get("/outcomes/graft-survival", response_model=GraftSurvivalRate)
async def get_graft_survival(organ: OrganType = Query(...)):
    """
    Get graft survival rates for a specific organ type.
    """
    return GraftSurvivalRate(
        organ=organ,
        one_year_survival_rate=0.96,
        three_year_survival_rate=0.88,
        five_year_survival_rate=0.79
    )

@router.post("/donors/register-organ", response_model=DonorOrganResponse)
async def register_organ(organ_data: RegisterOrganRequest):
    """
    Register a new donor organ.
    """
    # Mock response
    return DonorOrganResponse(
        id=202,
        donor_id=organ_data.donor_id,
        organ_type=organ_data.organ_type,
        blood_type=organ_data.blood_type,
        condition_score=organ_data.condition_score,
        is_available=True
    )

@router.post("/matching/run", response_model=MatchingResponse)
async def run_matching(matching_data: RunMatchingRequest):
    """
    Run the matching algorithm for a specific organ.
    """
    # Mock response
    return MatchingResponse(
        match_id=555,
        recipient_id="P12345",
        score=0.98,
        status="Match Found"
    )
