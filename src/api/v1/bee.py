from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from src.database import get_db
from src.models.bee_models import Apiary, Hive, Inspection, ColonyStrength, HiveStatus, BroodPattern
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from pydantic import field_validator

router = APIRouter()

# --- Schemas ---

class GeoJSONPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float] # [longitude, latitude]

class ApiaryBase(BaseModel):
    name: str
    owner_id: int
    hive_count: int = 0
    primary_forage: Optional[str] = None
    altitude_m: Optional[float] = None
    climate_zone: Optional[str] = None

class ApiaryCreate(ApiaryBase):
    location: Any # Expecting GeoJSON or WKT, handled in logic

class ApiaryResponse(ApiaryBase):
    id: int
    registered_since: datetime
    location: Any # WKBElement or GeoJSON dict

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    @field_validator("location", mode="before")
    @classmethod
    def serialize_location(cls, v: Any) -> Any:
        # Check if v is a WKBElement (from geoalchemy2)
        if hasattr(v, "desc") or (hasattr(v, "geom_type") and hasattr(v, "srid")):
             try:
                 shape = to_shape(v)
                 return mapping(shape)
             except Exception:
                 return v
        return v

class HiveBase(BaseModel):
    hive_number: str
    queen_age_months: Optional[int] = None
    colony_strength: Optional[ColonyStrength] = None
    weight_kg: Optional[float] = None
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    sound_level_db: Optional[float] = None
    status: HiveStatus = HiveStatus.ACTIVE

class HiveResponse(HiveBase):
    id: int
    apiary_id: int

    model_config = ConfigDict(from_attributes=True)

class InspectionBase(BaseModel):
    inspector_id: int
    date: datetime = Field(default_factory=datetime.utcnow)
    brood_pattern: Optional[BroodPattern] = None
    queen_seen: bool = False
    disease_signs: Optional[Dict[str, Any]] = None
    honey_supers: int = 0
    varroa_count: Optional[int] = None
    notes: Optional[str] = None
    action_taken: Optional[str] = None

class InspectionCreate(InspectionBase):
    hive_id: int

class InspectionResponse(InspectionBase):
    id: int
    hive_id: int

    model_config = ConfigDict(from_attributes=True)

# --- Endpoints ---

@router.get("/apiaries", response_model=List[ApiaryResponse])
async def get_apiaries(region: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Apiary)
    if region:
        query = query.filter(Apiary.climate_zone == region)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/apiaries/{id}/overview", response_model=ApiaryResponse)
async def get_apiary_overview(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Apiary).where(Apiary.id == id))
    apiary = result.scalar_one_or_none()
    if not apiary:
        raise HTTPException(status_code=404, detail="Apiary not found")
    return apiary

@router.get("/hives/{apiary_id}/status-grid", response_model=List[HiveResponse])
async def get_hives_status_grid(apiary_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Hive).where(Hive.apiary_id == apiary_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/hives/{id}/telemetry")
async def get_hive_telemetry(id: int, days: int = 7, db: AsyncSession = Depends(get_db)):
    # Mock telemetry data
    return {
        "hive_id": id,
        "days": days,
        "telemetry": [
            {"date": "2023-10-27T10:00:00Z", "temperature_c": 35.2, "humidity_pct": 60.5},
            {"date": "2023-10-27T11:00:00Z", "temperature_c": 35.5, "humidity_pct": 59.8},
        ]
    }

@router.post("/inspections/log", response_model=InspectionResponse)
async def log_inspection(inspection: InspectionCreate, db: AsyncSession = Depends(get_db)):
    db_inspection = Inspection(**inspection.model_dump())
    db.add(db_inspection)
    await db.commit()
    await db.refresh(db_inspection)
    return db_inspection

@router.get("/inspections/{hive_id}/history", response_model=List[InspectionResponse])
async def get_inspection_history(hive_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Inspection).where(Inspection.hive_id == hive_id).order_by(Inspection.date.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/analytics/colony-loss-rate")
async def get_colony_loss_rate():
    return {"region": "global", "loss_rate_pct": 15.2, "period": "last_year"}

@router.get("/alerts/swarm-predictions")
async def get_swarm_predictions():
    return [
        {"hive_id": 101, "probability": 0.85, "predicted_at": "2023-10-28"},
        {"hive_id": 204, "probability": 0.65, "predicted_at": "2023-10-29"}
    ]

@router.get("/forage/bloom-calendar")
async def get_bloom_calendar(location: str = Query(..., description="Location coordinate or region")):
    return {
        "location": location,
        "blooms": [
            {"plant": "Clover", "start_month": "May", "end_month": "August"},
            {"plant": "Goldenrod", "start_month": "August", "end_month": "October"}
        ]
    }
