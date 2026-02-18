from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models.pet_models import Pet, VetVisit, Vaccination, Species
from src.schemas.pet_schemas import (
    PetHealthReport,
    VaccineReminder,
    HealthAlert,
    PetResponse,
    VetVisitResponse,
    VaccinationResponse
)

async def calculate_vaccination_schedule(db: AsyncSession, pet_id: int) -> list[VaccineReminder]:
    stmt = select(Vaccination).where(Vaccination.pet_id == pet_id)
    result = await db.execute(stmt)
    vaccinations = result.scalars().all()

    reminders = []
    today = date.today()

    for v in vaccinations:
        if v.next_due:
            is_overdue = v.next_due < today
            reminders.append(VaccineReminder(
                vaccine_name=v.vaccine_name,
                due_date=v.next_due,
                overdue=is_overdue
            ))

    return reminders

async def detect_weight_anomaly(db: AsyncSession, pet_id: int) -> HealthAlert | None:
    stmt = select(Pet).where(Pet.id == pet_id)
    result = await db.execute(stmt)
    pet = result.scalar_one_or_none()

    if not pet:
        return None

    # Mock anomaly detection based on species thresholds
    thresholds = {
        Species.dog: (0.5, 100.0),
        Species.cat: (0.5, 20.0),
        Species.bird: (0.01, 5.0),
        Species.rabbit: (0.5, 10.0)
    }

    min_w, max_w = thresholds.get(pet.species, (0, 1000))

    if pet.weight_kg < min_w or pet.weight_kg > max_w:
        return HealthAlert(
            severity="High",
            message=f"Abnormal weight for {pet.species}: {pet.weight_kg}kg",
            timestamp=datetime.now(timezone.utc)
        )

    return None

async def generate_health_report(db: AsyncSession, pet_id: int) -> PetHealthReport:
    # Fetch Pet with relationships
    # We can use selectinload or separate queries. Separate is often safer with async if not configured perfectly.
    # But let's try separate for clarity.

    stmt = select(Pet).where(Pet.id == pet_id)
    result = await db.execute(stmt)
    pet = result.scalar_one_or_none()

    if not pet:
        raise ValueError(f"Pet with id {pet_id} not found")

    # Recent visits
    stmt_visits = select(VetVisit).where(VetVisit.pet_id == pet_id).order_by(VetVisit.visit_date.desc()).limit(5)
    result_visits = await db.execute(stmt_visits)
    visits = result_visits.scalars().all()

    # Vaccinations
    stmt_vacs = select(Vaccination).where(Vaccination.pet_id == pet_id)
    result_vacs = await db.execute(stmt_vacs)
    vaccinations = result_vacs.scalars().all()

    # Calculate schedule
    upcoming = await calculate_vaccination_schedule(db, pet_id)

    # Detect anomalies
    anomaly = await detect_weight_anomaly(db, pet_id)
    alerts = [anomaly] if anomaly else []

    return PetHealthReport(
        pet_info=PetResponse.model_validate(pet),
        recent_visits=[VetVisitResponse.model_validate(v) for v in visits],
        vaccination_status=[VaccinationResponse.model_validate(v) for v in vaccinations],
        alerts=alerts,
        upcoming_vaccines=upcoming
    )
