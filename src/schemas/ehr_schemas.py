from pydantic import BaseModel, ConfigDict
from typing import Dict, Optional, List
from src.models.ehr_models import LabStatus, ReferralUrgency

class Interaction(BaseModel):
    severity: str
    description: str

class PatientSummary(BaseModel):
    patient_id: str
    allergies: Dict = {}
    chronic_conditions: Dict = {}
    medications: Dict = {}
    blood_type: Optional[str] = None
    emergency_contact: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ReferralAccept(BaseModel):
    referral_id: int
    accepted: bool

class ReferralResponse(BaseModel):
    id: int
    patient_id: str
    consultation_id: str
    referred_to_specialty: str
    urgency: ReferralUrgency
    clinical_summary: str
    accepted: bool

    model_config = ConfigDict(from_attributes=True)

class LabOrderCreate(BaseModel):
    consultation_id: str
    tests: Dict
    lab_id: str

class LabOrderResponse(LabOrderCreate):
    id: int
    status: LabStatus
    results_uri: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PatientRecordCreate(PatientSummary):
    pass

class PatientRecordResponse(PatientSummary):
    id: int

    model_config = ConfigDict(from_attributes=True)
