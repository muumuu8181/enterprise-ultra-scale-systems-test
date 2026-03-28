from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from src.models.pharmacy_models import MedicationForm, PrescriptionStatus

class MedicationCreate(BaseModel):
    id: str
    name: str
    generic_name: str
    ndc_code: str
    drug_class: str
    form: MedicationForm
    strength: str
    manufacturer: str
    requires_rx: bool = True
    controlled_schedule: Optional[int] = None
    stock_quantity: int = 0
    reorder_level: int = 10

    model_config = ConfigDict(from_attributes=True)

class MedicationResponse(MedicationCreate):
    pass

class PrescriptionCreate(BaseModel):
    id: str
    patient_id: str
    prescriber_id: str
    medication_id: str
    dosage: str
    frequency: str
    quantity: int
    refills_allowed: int = 0
    rx_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PrescriptionResponse(PrescriptionCreate):
    refills_used: int
    status: PrescriptionStatus

class DispensingCreate(BaseModel):
    id: str
    prescription_id: str
    pharmacist_id: str
    quantity: int
    lot_number: str
    expiry_date: datetime
    patient_counseled: bool = False
    copay_amount: float

    model_config = ConfigDict(from_attributes=True)

class DispensingResponse(DispensingCreate):
    dispensed_at: datetime

class InventoryUpdate(BaseModel):
    medication_id: str
    quantity_change: int

    model_config = ConfigDict(from_attributes=True)

class AnalyticsResponse(BaseModel):
    period: str
    total_dispensed: int
    total_revenue: float
    top_medications: List[str]

    model_config = ConfigDict(from_attributes=True)
