from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from src.database import get_db
from src.models.debris_models import DebrisObject, ConjunctionEvent, ManeuverPlan, DebrisObjectType, ConjunctionStatus, ManeuverStatus

router = APIRouter()

# --- Schemas ---

class DebrisObjectBase(BaseModel):
    norad_id: int
    object_type: DebrisObjectType
    size_cm: float
    mass_kg: float
    orbit_altitude_km: float
    inclination_deg: float
    tle_line1: str
    tle_line2: str

class DebrisObjectCreate(DebrisObjectBase):
    pass

class DebrisObjectResponse(DebrisObjectBase):
    id: int
    last_observed: datetime

    class Config:
        from_attributes = True

class TrajectoryPoint(BaseModel):
    time: datetime
    latitude: float
    longitude: float
    altitude_km: float

class ConjunctionAssessmentRequest(BaseModel):
    primary_object_id: int
    secondary_object_id: int
    tca: datetime
    miss_distance_m: float
    collision_probability: float

class ConjunctionResponse(BaseModel):
    id: int
    primary_object_id: int
    secondary_object_id: int
    tca: datetime
    miss_distance_m: float
    collision_probability: float
    status: ConjunctionStatus

    class Config:
        from_attributes = True

class ManeuverPlanRequest(BaseModel):
    conjunction_id: int
    satellite_id: int
    delta_v: float
    burn_duration_sec: float
    execution_time: datetime
    fuel_cost_kg: float

class ManeuverPlanResponse(BaseModel):
    id: int
    conjunction_id: int
    satellite_id: int
    delta_v: float
    burn_duration_sec: float
    execution_time: datetime
    fuel_cost_kg: float
    status: ManeuverStatus

    class Config:
        from_attributes = True

class CatalogStatistics(BaseModel):
    total_objects: int
    by_type: Dict[str, int]

class ReentryPrediction(BaseModel):
    object_id: int
    norad_id: int
    reentry_time: datetime
    location: str
    probability: float

# --- Endpoints ---

@router.get("/objects", response_model=List[DebrisObjectResponse])
async def get_objects(
    orbit_range: Optional[str] = Query(None, description="Range of orbit altitude in km, e.g. '100-500'"),
    object_type: Optional[DebrisObjectType] = Query(None, alias="type"),
    db: AsyncSession = Depends(get_db)
):
    query = select(DebrisObject)
    if object_type:
        query = query.filter(DebrisObject.object_type == object_type)

    if orbit_range:
        try:
            min_alt, max_alt = map(float, orbit_range.split("-"))
            query = query.filter(DebrisObject.orbit_altitude_km >= min_alt, DebrisObject.orbit_altitude_km <= max_alt)
        except ValueError:
            pass

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/objects/{norad_id}/trajectory", response_model=List[TrajectoryPoint])
async def get_trajectory(norad_id: int = Path(...), db: AsyncSession = Depends(get_db)):
    return [
        TrajectoryPoint(time=datetime.utcnow(), latitude=0.0, longitude=0.0, altitude_km=400.0)
    ]

@router.get("/conjunctions/upcoming", response_model=List[ConjunctionResponse])
async def get_upcoming_conjunctions(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db)
):
    # Mocking date filtering for simplicity
    query = select(ConjunctionEvent)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/conjunctions/assess", response_model=ConjunctionResponse)
async def assess_conjunction(
    assessment: ConjunctionAssessmentRequest,
    db: AsyncSession = Depends(get_db)
):
    event = ConjunctionEvent(
        primary_object_id=assessment.primary_object_id,
        secondary_object_id=assessment.secondary_object_id,
        tca=assessment.tca,
        miss_distance_m=assessment.miss_distance_m,
        collision_probability=assessment.collision_probability,
        status=ConjunctionStatus.monitoring
    )
    if event.collision_probability > 0.01:
        event.status = ConjunctionStatus.alert
    elif event.collision_probability > 0.001:
        event.status = ConjunctionStatus.warning

    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event

@router.post("/maneuvers/plan", response_model=ManeuverPlanResponse)
async def plan_maneuver(
    plan: ManeuverPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    new_plan = ManeuverPlan(
        conjunction_id=plan.conjunction_id,
        satellite_id=plan.satellite_id,
        delta_v=plan.delta_v,
        burn_duration_sec=plan.burn_duration_sec,
        execution_time=plan.execution_time,
        fuel_cost_kg=plan.fuel_cost_kg,
        status=ManeuverStatus.planned
    )
    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)

    conjunction = await db.get(ConjunctionEvent, plan.conjunction_id)
    if conjunction:
        conjunction.status = ConjunctionStatus.maneuver_planned
        await db.commit()

    return new_plan

@router.put("/maneuvers/{id}/approve", response_model=ManeuverPlanResponse)
async def approve_maneuver(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    plan = await db.get(ManeuverPlan, id)
    if not plan:
        raise HTTPException(status_code=404, detail="Maneuver plan not found")

    plan.status = ManeuverStatus.approved
    await db.commit()
    await db.refresh(plan)
    return plan

@router.get("/catalog/statistics", response_model=CatalogStatistics)
async def get_catalog_statistics(db: AsyncSession = Depends(get_db)):
    return CatalogStatistics(
        total_objects=12345,
        by_type={"rocket_body": 1000, "payload": 2000, "fragment": 9345}
    )

@router.get("/reentry/predictions", response_model=List[ReentryPrediction])
async def get_reentry_predictions():
    return [
        ReentryPrediction(
            object_id=1,
            norad_id=12345,
            reentry_time=datetime.utcnow(),
            location="Pacific Ocean",
            probability=0.95
        )
    ]
