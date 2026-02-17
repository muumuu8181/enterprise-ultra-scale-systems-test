from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.database import get_db
from src.models.pet_models import Pet, VetVisit, Vaccination
from src.schemas.pet_schemas import (
    PetCreate, PetResponse,
    VetVisitCreate, VetVisitResponse,
    VaccinationCreate, VaccinationResponse,
    PetHealthReport, VaccineReminder,
    WeightLogRequest, HealthAlert
)
from src.services import health_service

router = APIRouter(prefix="/pets", tags=["pets"])

@router.post("/register", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
async def register_pet(pet_in: PetCreate, db: AsyncSession = Depends(get_db)):
    pet = Pet(**pet_in.model_dump())
    db.add(pet)
    await db.commit()
    await db.refresh(pet)
    return pet

@router.get("/{id}/health-summary", response_model=PetHealthReport)
async def get_health_summary(id: int, db: AsyncSession = Depends(get_db)):
    try:
        report = await health_service.generate_health_report(db, id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{id}/vaccination-passport", response_model=List[VaccinationResponse])
async def get_vaccination_passport(id: int, db: AsyncSession = Depends(get_db)):
    pet = await db.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    stmt = select(Vaccination).where(Vaccination.pet_id == id)
    result = await db.execute(stmt)
    vaccinations = result.scalars().all()
    return vaccinations

@router.post("/{id}/vet-visits", response_model=VetVisitResponse, status_code=status.HTTP_201_CREATED)
async def create_vet_visit(id: int, visit_in: VetVisitCreate, db: AsyncSession = Depends(get_db)):
    pet = await db.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    visit = VetVisit(pet_id=id, **visit_in.model_dump())
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    return visit

@router.post("/{id}/weight-log", response_model=HealthAlert | None)
async def log_weight(id: int, weight_in: WeightLogRequest, db: AsyncSession = Depends(get_db)):
    pet = await db.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    pet.weight_kg = weight_in.weight_kg
    await db.commit()
    await db.refresh(pet)

    # Check for anomaly
    anomaly = await health_service.detect_weight_anomaly(db, id)
    return anomaly

@router.get("/{id}/reminders", response_model=List[VaccineReminder])
async def get_reminders(id: int, db: AsyncSession = Depends(get_db)):
    pet = await db.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    reminders = await health_service.calculate_vaccination_schedule(db, id)
    return reminders
