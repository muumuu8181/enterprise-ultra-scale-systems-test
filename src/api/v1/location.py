from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import from_shape
from shapely.geometry import shape, Point, Polygon
from src.database import get_db
from src.models.location_models import UserLocation, GeofenceZone, GeofenceEvent
from src.services import geofence_service
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

router = APIRouter(prefix="", tags=["location"])

# Schemas
class UserLocationBase(BaseModel):
    latitude: float
    longitude: float
    accuracy_m: float
    timestamp: Optional[datetime] = None
    source: str = "gps"

class UserLocationUpdate(UserLocationBase):
    user_id: str

class UserLocationResponse(UserLocationBase):
    id: int
    user_id: str
    model_config = ConfigDict(from_attributes=True)

class GeofenceCreate(BaseModel):
    name: str
    geometry: Dict[str, Any] # GeoJSON
    zone_type: str = "polygon" # circle/polygon
    trigger_on: str = "enter,exit"
    dwell_seconds: Optional[int] = None
    radius_m: Optional[float] = None

class GeofenceResponse(BaseModel):
    id: int
    name: str
    # returning geometry as GeoJSON might require custom serializer or just dict
    # We will skip geometry in response or return it if requested?
    # Usually returning GeoJSON is expected.
    # However, formatting WKB to GeoJSON requires conversion.
    # We'll omit it or handle it if easy.
    # Let's return a simplified representation or string for now to avoid complexity
    # or use a property.
    zone_type: str
    trigger_on: str
    model_config = ConfigDict(from_attributes=True)

class GeofenceEventResponse(BaseModel):
    id: int
    user_id: str
    zone_id: int
    event_type: str
    triggered_at: datetime
    metadata_info: Optional[Dict[str, Any]] = Field(None, alias="metadata")
    model_config = ConfigDict(from_attributes=True)

class SessionTrack(BaseModel):
    session_id: str
    user_id: str
    locations: List[UserLocationBase]

# Endpoints

@router.post("/locations/update")
async def update_locations(updates: List[UserLocationUpdate], db: AsyncSession = Depends(get_db)):
    """
    Batch update user locations
    """
    new_locations = []
    events = []

    # Sort updates by timestamp to process logic correctly
    # If timestamp is missing, use current time
    for u in updates:
        if not u.timestamp:
            u.timestamp = datetime.utcnow()

    sorted_updates = sorted(updates, key=lambda x: x.timestamp)

    for u in sorted_updates:
        point = f"POINT({u.longitude} {u.latitude})"
        loc = UserLocation(
            user_id=u.user_id,
            latitude=u.latitude,
            longitude=u.longitude,
            accuracy_m=u.accuracy_m,
            timestamp=u.timestamp,
            source=u.source,
            geom=WKTElement(point, srid=4326)
        )
        db.add(loc)
        new_locations.append(loc)

        # Check geofences
        # We await here, which might be slow for large batches.
        # Ideally this is async background task.
        evts = await geofence_service.check_geofences(db, u.user_id, u.latitude, u.longitude)
        events.extend(evts)

    await db.commit()
    return {"message": f"Processed {len(updates)} updates", "events_generated": len(events)}

@router.get("/users/{user_id}/last-location", response_model=UserLocationResponse)
async def get_last_location(user_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(UserLocation).where(UserLocation.user_id == user_id).order_by(UserLocation.timestamp.desc()).limit(1)
    result = await db.execute(stmt)
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc

@router.post("/geofences/create", response_model=GeofenceResponse)
async def create_geofence(geo: GeofenceCreate, db: AsyncSession = Depends(get_db)):
    # Convert GeoJSON to WKT/WKB
    try:
        s = shape(geo.geometry)
        # s is a shapely geometry
        # We need to convert it to WKTElement or WKBElement for GeoAlchemy2
        # WKT is easier
        wkt = s.wkt
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid GeoJSON: {e}")

    geofence = GeofenceZone(
        name=geo.name,
        geometry=WKTElement(wkt, srid=4326),
        zone_type=geo.zone_type,
        trigger_on=geo.trigger_on,
        dwell_seconds=geo.dwell_seconds,
        radius_m=geo.radius_m
    )
    db.add(geofence)
    await db.commit()
    await db.refresh(geofence)
    return geofence

@router.get("/geofences/nearby", response_model=List[GeofenceResponse])
async def get_nearby_geofences(
    lat: float,
    lon: float,
    radius_m: float,
    db: AsyncSession = Depends(get_db)
):
    # Reuse find_points_of_interest logic or similar query
    # Since find_points_of_interest returns POIs (simplified), we query directly here for GeofenceResponse
    # But GeofenceResponse doesn't include geometry or radius, so it matches the model.

    # We can reuse the service function 'find_points_of_interest' but it returns POI objects.
    # So we write the query here.

    from geoalchemy2.types import Geography
    from sqlalchemy import func

    point = WKTElement(f"POINT({lon} {lat})", srid=4326)

    stmt = select(GeofenceZone).where(
        func.ST_DWithin(
            func.CAST(GeofenceZone.geometry, Geography),
            func.CAST(point, Geography),
            radius_m
        )
    )
    result = await db.execute(stmt)
    zones = result.scalars().all()
    return zones

@router.get("/geofences/{id}/events", response_model=List[GeofenceEventResponse])
async def get_geofence_events(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(GeofenceEvent).where(GeofenceEvent.zone_id == id).order_by(GeofenceEvent.triggered_at.desc())
    result = await db.execute(stmt)
    events = result.scalars().all()
    return events

@router.post("/locations/track-session")
async def track_session(session: SessionTrack, db: AsyncSession = Depends(get_db)):
    """
    Track a session of points. Similar to update but with session context.
    """
    updates = []
    for loc in session.locations:
        u = UserLocationUpdate(
            user_id=session.user_id,
            **loc.model_dump()
        )
        updates.append(u)

    return await update_locations(updates, db)
