from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime, time
from pydantic import BaseModel, ConfigDict

from src.database import get_db
from src.models.vet_models import Pet, Appointment, MedicalRecord, Species, PetStatus, AppointmentType, AppointmentStatus

router = APIRouter(prefix="/vet", tags=["vet"])

# --- Pydantic Schemas ---

class PetBase(BaseModel):
    name: str
    species: Species
    breed: Optional[str] = None
    sex: Optional[str] = None
    birth_date: Optional[date] = None
    weight_kg: Optional[float] = None
    microchip_id: Optional[str] = None
    owner_id: str
    allergies: List[str] = []
    status: PetStatus = PetStatus.active

class PetCreate(PetBase):
    pass

class PetResponse(PetBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class AppointmentBase(BaseModel):
    pet_id: int
    vet_id: str
    appointment_type: AppointmentType
    scheduled_at: datetime
    duration_min: int = 30
    notes: Optional[str] = None
    status: AppointmentStatus = AppointmentStatus.scheduled

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentResponse(AppointmentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class MedicalRecordBase(BaseModel):
    pet_id: int
    appointment_id: int
    diagnosis: str
    treatments: List[str] = []
    prescriptions: List[str] = []
    lab_results: Dict[str, Any] = {}
    vitals: Dict[str, Any] = {}
    next_followup: Optional[date] = None

class MedicalRecordCreate(MedicalRecordBase):
    pass

class MedicalRecordResponse(MedicalRecordBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Endpoints ---

@router.post("/pets", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
def create_pet(pet: PetCreate, db: Session = Depends(get_db)):
    db_pet = Pet(**pet.model_dump())
    db.add(db_pet)
    db.commit()
    db.refresh(db_pet)
    return db_pet

@router.get("/pets", response_model=List[PetResponse])
def list_pets(
    owner_id: Optional[str] = None,
    species: Optional[Species] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Pet)
    if owner_id:
        query = query.filter(Pet.owner_id == owner_id)
    if species:
        query = query.filter(Pet.species == species)
    return query.all()

@router.get("/pets/{id}/medical-history", response_model=List[MedicalRecordResponse])
def get_medical_history(id: int, db: Session = Depends(get_db)):
    pet = db.query(Pet).filter(Pet.id == id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    return db.query(MedicalRecord).filter(MedicalRecord.pet_id == id).all()

@router.post("/appointments/book", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    pet = db.query(Pet).filter(Pet.id == appointment.pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    db_appointment = Appointment(**appointment.model_dump())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

@router.get("/appointments/today", response_model=List[AppointmentResponse])
def get_today_appointments(vet_id: Optional[str] = None, db: Session = Depends(get_db)):
    today = date.today()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)

    query = db.query(Appointment).filter(Appointment.scheduled_at >= start_of_day, Appointment.scheduled_at <= end_of_day)
    if vet_id:
        query = query.filter(Appointment.vet_id == vet_id)
    return query.all()

@router.post("/records/create", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def create_medical_record(record: MedicalRecordCreate, db: Session = Depends(get_db)):
    # Check if appointment exists
    appointment = db.query(Appointment).filter(Appointment.id == record.appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    db_record = MedicalRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.get("/records/{pet_id}/vaccinations", response_model=List[MedicalRecordResponse])
def get_vaccinations(pet_id: int, db: Session = Depends(get_db)):
    # Join with appointment to filter by type
    records = db.query(MedicalRecord).join(Appointment).filter(
        MedicalRecord.pet_id == pet_id,
        Appointment.appointment_type == AppointmentType.vaccination
    ).all()
    return records

@router.get("/inventory/medications")
def check_inventory(low_stock: bool = False):
    meds = [
        {"name": "Amoxicillin", "stock": 100, "low_stock": False},
        {"name": "Rabies Vaccine", "stock": 5, "low_stock": True},
        {"name": "Meloxicam", "stock": 50, "low_stock": False},
    ]
    if low_stock:
        return [m for m in meds if m["low_stock"]]
    return meds

@router.get("/analytics/revenue")
def get_revenue(period: str = "monthly"):
    return {"period": period, "revenue": 15000.00, "currency": "USD"}

@router.post("/prescriptions/refill")
def refill_prescription(prescription_id: int):
    return {"status": "refill_requested", "prescription_id": prescription_id, "ready_date": date.today()}
