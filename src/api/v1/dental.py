from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum

from src.models.dental_models import TreatmentStatus, AppointmentType, AppointmentStatus

router = APIRouter()

# --- Pydantic Schemas ---

class PatientBase(BaseModel):
    name: str
    dob: date
    insurance_id: Optional[str] = None
    allergies: List[str] = []
    medical_conditions: List[str] = []

class PatientResponse(PatientBase):
    id: int
    last_xray_date: Optional[date] = None
    next_cleaning_due: Optional[date] = None
    balance_due: float

class TreatmentPlanCreate(BaseModel):
    patient_id: int
    dentist_id: int
    procedures: List[Dict[str, Any]] = []  # Detailed procedure info
    total_cost: float
    insurance_coverage: float
    patient_responsibility: float
    valid_until: Optional[date] = None

class TreatmentPlanResponse(TreatmentPlanCreate):
    id: int
    status: TreatmentStatus

class AppointmentBook(BaseModel):
    patient_id: int
    dentist_id: Optional[int] = None
    hygienist_id: Optional[int] = None
    appointment_type: AppointmentType
    scheduled_at: datetime
    chair_number: int
    duration_min: int

class AppointmentResponse(AppointmentBook):
    id: int
    status: AppointmentStatus

class SupplyItem(BaseModel):
    id: int
    name: str
    quantity: int
    reorder_level: int

class ProviderProduction(BaseModel):
    provider_id: int
    provider_name: str
    production_amount: float

class ClaimSubmission(BaseModel):
    treatment_plan_id: int
    insurance_id: str
    amount: float

class ClaimResponse(BaseModel):
    claim_id: str
    status: str

# --- Endpoints ---

@router.get("/patients/{id}/dental-chart", response_model=Dict[str, Any])
async def get_dental_chart(id: int):
    """
    Get dental chart for a patient.
    """
    # Mock response
    return {
        "patient_id": id,
        "chart": {
            "1": "healthy",
            "2": "filling",
            "3": "implant",
            # ... other teeth
        }
    }

@router.get("/patients/{id}/history", response_model=List[TreatmentPlanResponse])
async def get_patient_history(id: int):
    """
    Get treatment history for a patient.
    """
    # Mock response
    return []

@router.post("/treatment-plans/create", response_model=TreatmentPlanResponse)
async def create_treatment_plan(plan: TreatmentPlanCreate):
    """
    Create a new treatment plan.
    """
    # Mock response
    return TreatmentPlanResponse(
        id=123,
        **plan.model_dump(),
        status=TreatmentStatus.PROPOSED
    )

@router.get("/treatment-plans/{id}/insurance-estimate", response_model=Dict[str, Any])
async def get_insurance_estimate(id: int):
    """
    Get insurance estimate for a treatment plan.
    """
    # Mock response
    return {
        "treatment_plan_id": id,
        "estimated_coverage": 500.00,
        "patient_share": 200.00
    }

@router.post("/appointments/book", response_model=AppointmentResponse)
async def book_appointment(appointment: AppointmentBook):
    """
    Book a new appointment.
    """
    # Mock response
    return AppointmentResponse(
        id=456,
        **appointment.model_dump(),
        status=AppointmentStatus.SCHEDULED
    )

@router.get("/appointments/today", response_model=List[AppointmentResponse])
async def get_appointments_today(dentist: Optional[int] = None):
    """
    Get appointments for today, optionally filtered by dentist.
    """
    # Mock response
    return []

@router.get("/inventory/supplies", response_model=List[SupplyItem])
async def check_inventory(low_stock: bool = Query(False)):
    """
    Check inventory supplies.
    """
    # Mock response
    if low_stock:
        return [
            SupplyItem(id=1, name="Gloves", quantity=10, reorder_level=50),
            SupplyItem(id=2, name="Masks", quantity=20, reorder_level=100)
        ]
    return []

@router.get("/analytics/production-by-provider", response_model=List[ProviderProduction])
async def get_production_by_provider():
    """
    Get production analytics by provider.
    """
    # Mock response
    return [
        ProviderProduction(provider_id=1, provider_name="Dr. Smith", production_amount=15000.00),
        ProviderProduction(provider_id=2, provider_name="Dr. Jones", production_amount=12000.00)
    ]

@router.post("/billing/submit-claim", response_model=ClaimResponse)
async def submit_claim(claim: ClaimSubmission):
    """
    Submit an insurance claim.
    """
    # Mock response
    return ClaimResponse(claim_id="CLM-789", status="submitted")
