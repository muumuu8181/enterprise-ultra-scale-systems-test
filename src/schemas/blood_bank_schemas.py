from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional, List, Dict
from src.models.blood_bank_models import BloodType, BloodComponent, BloodUnitStatus, UrgencyLevel, RequestStatus, CrossmatchStatus

# Base Schemas

class DonorBase(BaseModel):
    name: str
    blood_type: BloodType
    eligible: bool = True
    deferral_reason: Optional[str] = None
    contact_info: Optional[Dict] = None

class BloodUnitBase(BaseModel):
    donor_id: int
    blood_type: BloodType
    component: BloodComponent
    collection_date: date
    expiry_date: date
    volume_ml: int
    storage_location: str
    status: BloodUnitStatus = BloodUnitStatus.COLLECTED

class TransfusionRequestBase(BaseModel):
    patient_id: str
    hospital_id: str
    blood_type: BloodType
    component: BloodComponent
    units_needed: int
    urgency: UrgencyLevel
    crossmatch_status: CrossmatchStatus = CrossmatchStatus.PENDING
    status: RequestStatus = RequestStatus.REQUESTED

# Create Schemas

class DonorCreate(DonorBase):
    pass

class BloodUnitCreate(BloodUnitBase):
    pass

class TransfusionRequestCreate(TransfusionRequestBase):
    pass

# Response Schemas

class BloodUnitResponse(BloodUnitBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class DonorResponse(DonorBase):
    id: int
    last_donation_date: Optional[date] = None
    total_donations: int = 0
    donations: List[BloodUnitResponse] = []
    model_config = ConfigDict(from_attributes=True)

class TransfusionRequestResponse(TransfusionRequestBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class InventoryStats(BaseModel):
    total_units: int
    by_blood_type: Dict[BloodType, int]
    by_component: Dict[BloodComponent, int]
    critical_levels: List[str]

class UsageTrend(BaseModel):
    period: str
    usage_count: int
