from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from src.database import get_db
from src.models.vessel_models import Vessel, AISPosition, Port, VesselType
from pydantic import BaseModel, ConfigDict
from geoalchemy2.functions import ST_Within, ST_MakeEnvelope

router = APIRouter(prefix="/vessels", tags=["vessels"])

class VesselResponse(BaseModel):
    id: int
    mmsi: int
    vessel_name: str
    vessel_type: VesselType
    flag_country: str
    length_m: float
    gross_tonnage: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)

class PositionResponse(BaseModel):
    id: int
    vessel_id: int
    timestamp: datetime
    latitude: float
    longitude: float
    speed_knots: float
    course: float
    navigational_status: str
    draught: float

    model_config = ConfigDict(from_attributes=True)

class PortCallResponse(BaseModel):
    port_name: str
    arrival_time: datetime
    departure_time: Optional[datetime]
    duration_hours: float

@router.get("/search", response_model=List[VesselResponse])
async def search_vessels(
    name: Optional[str] = None,
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Vessel)
    if name:
        query = query.where(Vessel.vessel_name.ilike(f"%{name}%"))
    if type:
        try:
            # Try to match enum
            v_type = VesselType(type.lower())
            query = query.where(Vessel.vessel_type == v_type)
        except ValueError:
            # If invalid type provided, maybe return empty list
            return []

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{mmsi}/track", response_model=List[PositionResponse])
async def get_vessel_track(
    mmsi: int,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    vessel_stmt = select(Vessel).where(Vessel.mmsi == mmsi)
    vessel_res = await db.execute(vessel_stmt)
    vessel = vessel_res.scalar_one_or_none()

    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")

    track_stmt = select(AISPosition).where(AISPosition.vessel_id == vessel.id).order_by(desc(AISPosition.timestamp)).limit(limit)
    track_res = await db.execute(track_stmt)
    return track_res.scalars().all()

@router.get("/{mmsi}/current-position", response_model=PositionResponse)
async def get_current_position(
    mmsi: int,
    db: AsyncSession = Depends(get_db)
):
    vessel_stmt = select(Vessel).where(Vessel.mmsi == mmsi)
    vessel_res = await db.execute(vessel_stmt)
    vessel = vessel_res.scalar_one_or_none()

    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")

    pos_stmt = select(AISPosition).where(AISPosition.vessel_id == vessel.id).order_by(desc(AISPosition.timestamp)).limit(1)
    pos_res = await db.execute(pos_stmt)
    pos = pos_res.scalar_one_or_none()

    if not pos:
        raise HTTPException(status_code=404, detail="No position data found")

    return pos

@router.get("/in-area", response_model=List[VesselResponse])
async def get_vessels_in_area(
    bbox: str = Query(..., description="min_lon,min_lat,max_lon,max_lat"),
    db: AsyncSession = Depends(get_db)
):
    try:
        min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bbox format")

    # Using ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
    envelope = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)

    # Find distinct vessels that have positions in this area
    # Note: Ideally we filter by recent positions (e.g. last 24h)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    stmt = select(Vessel).join(AISPosition).where(
        ST_Within(AISPosition.location, envelope),
        AISPosition.timestamp >= cutoff
    ).distinct()

    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{mmsi}/port-calls-history", response_model=List[PortCallResponse])
async def get_port_calls_history(
    mmsi: int,
    db: AsyncSession = Depends(get_db)
):
    # Placeholder implementation
    return []
