from fastapi import APIRouter, HTTPException, Depends, Query, Response
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.map_updater import MapUpdaterService
from src.models.map_models import RoadCondition

# Placeholder dependency for DB session
async def get_db():
    # TODO: Replace with actual database session dependency injection
    # In a real application, this would yield an AsyncSession from a configured sessionmaker
    # For the purpose of this file creation task without environment config, we yield None
    # Assuming the caller will mock this dependency in tests or override it.
    yield None

router = APIRouter()
service = MapUpdaterService()

class MapUpdate(BaseModel):
    section_id: str
    lane_data: Dict[str, Any]
    timestamp: str

class IncidentReport(BaseModel):
    location: Dict[str, float]  # e.g. {"lat": 1.0, "lon": 2.0}
    type: str
    severity: str

from pydantic import field_serializer

class RoadConditionResponse(BaseModel):
    id: int
    road_id: str
    condition_type: str
    location: Any
    valid_from: datetime
    valid_until: Optional[datetime]
    source: Optional[str]

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('location')
    def serialize_location(self, v: Any, _info):
        return str(v)

@router.get("/map/tiles/{z}/{x}/{y}")
async def get_map_tile(z: int, x: int, y: int, db: AsyncSession = Depends(get_db)):
    """
    Get HD map in tile format.
    """
    if db is None:
        # Prevent crash if executed without mocking
        # In real scenario, db is a valid session
        pass

    try:
        data = await service.fetch_tile(db, z, x, y)
    except Exception as e:
        # Fallback if DB is None or other error
        print(f"Error fetching tile: {e}")
        data = None

    if not data:
        raise HTTPException(status_code=404, detail="Tile not found")
    return Response(content=data, media_type="application/octet-stream")

@router.post("/map/updates")
async def update_map(update: MapUpdate, db: AsyncSession = Depends(get_db)):
    """
    Update map (section_id, lane_data JSON, timestamp).
    """
    result = await service.update_map_section(db, update.section_id, update.lane_data, update.timestamp)
    return result

@router.get("/map/road_conditions", response_model=List[RoadConditionResponse])
async def get_road_conditions(
    bounds: str = Query(..., description="Comma separated bbox: min_lon,min_lat,max_lon,max_lat"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get road conditions (wet/dry/ice/construction).
    """
    # TODO: Implement spatial query using GeoAlchemy2
    # 1. Parse bounds: min_lon, min_lat, max_lon, max_lat = map(float, bounds.split(','))
    # 2. Create envelope: box = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
    # 3. Query: stmt = select(RoadCondition).where(func.ST_Intersects(RoadCondition.location, box))
    # 4. Return results: (await db.execute(stmt)).scalars().all()

    # For now returning empty list as placeholder
    return []

@router.post("/map/incidents/report")
async def report_incident(report: IncidentReport, db: AsyncSession = Depends(get_db)):
    """
    Report incident (location, type, severity).
    """
    result = await service.report_incident(db, report.location, report.type, report.severity)
    return result
