from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional, List, Any
from src.models.pet_models import Species

class PetBase(BaseModel):
    owner_id: int
    name: str
    species: Species
    breed: Optional[str] = None
    birthdate: date
    weight_kg: float
    microchip_id: Optional[str] = None

class PetCreate(PetBase):
    pass

class PetResponse(PetBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class VetVisitBase(BaseModel):
    vet_id: int
    visit_date: date
    reason: str
    diagnosis: Optional[str] = None
    prescriptions: Optional[Any] = None
    next_visit: Optional[date] = None

class VetVisitCreate(VetVisitBase):
    pass

class VetVisitResponse(VetVisitBase):
    id: int
    pet_id: int

    model_config = ConfigDict(from_attributes=True)

class VaccinationBase(BaseModel):
    vaccine_name: str
    administered_date: date
    batch_number: Optional[str] = None
    next_due: Optional[date] = None
    vet_id: Optional[int] = None

class VaccinationCreate(VaccinationBase):
    pass

class VaccinationResponse(VaccinationBase):
    id: int
    pet_id: int

    model_config = ConfigDict(from_attributes=True)

class VaccineReminder(BaseModel):
    vaccine_name: str
    due_date: date
    overdue: bool

class HealthAlert(BaseModel):
    severity: str
    message: str
    timestamp: datetime

class PetHealthReport(BaseModel):
    pet_info: PetResponse
    recent_visits: List[VetVisitResponse]
    vaccination_status: List[VaccinationResponse]
    alerts: List[HealthAlert]
    upcoming_vaccines: List[VaccineReminder]

class WeightLogRequest(BaseModel):
    weight_kg: float
