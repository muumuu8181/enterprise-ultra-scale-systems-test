from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.services.routing_service import RoutingService
from src.models.routing_models import Route, TrafficSegment, ETARequest
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone

router = APIRouter(tags=["routing"])
service = RoutingService()

# Pydantic models
class RouteRequest(BaseModel):
    origin: str
    destination: str
    mode: str = "driving"
    avoid: List[str] = []

class RouteResponse(BaseModel):
    id: Optional[int] = None
    origin: str
    destination: str
    waypoints: List[Any]
    distance_km: float
    duration_min: float
    route_polyline: str
    transport_mode: str
    model_config = ConfigDict(from_attributes=True)

class TrafficSegmentResponse(BaseModel):
    id: Optional[int] = None
    segment_id: str
    road_name: str
    current_speed_kmh: float
    free_flow_speed: float
    congestion_level: int
    model_config = ConfigDict(from_attributes=True)

class ETARequestCreate(BaseModel):
    user_id: str
    origin: str
    destination: str
    mode: str = "driving"

class ETAResponse(BaseModel):
    id: Optional[int] = None
    user_id: str
    origin: str
    destination: str
    requested_at: datetime
    estimated_arrival: datetime
    actual_arrival: Optional[datetime] = None
    mode: str
    model_config = ConfigDict(from_attributes=True)

@router.post("/routes/calculate", response_model=RouteResponse)
async def calculate_route(request: RouteRequest, db: AsyncSession = Depends(get_db)):
    """
    Calculate route using A* and traffic data
    """
    route = await service.calculate_route(request.origin, request.destination, request.mode, request.avoid)
    # We return the route model instance directly, Pydantic handles serialization
    return route

@router.get("/routes/{id}/directions", response_model=RouteResponse)
async def get_route_directions(id: int, db: AsyncSession = Depends(get_db)):
    """
    Get route directions by ID
    """
    # Mock implementation: returning a dummy route as if fetched from DB
    # In reality: query DB by id
    route = await service.calculate_route("dummy_origin", "dummy_dest", "driving")
    # Simulate setting ID
    route.id = id
    return route

@router.get("/traffic/heatmap")
async def get_traffic_heatmap(bbox: str = Query(..., description="min_lon,min_lat,max_lon,max_lat")):
    """
    Get traffic heatmap data for a bounding box
    """
    try:
        parts = [float(x) for x in bbox.split(',')]
        if len(parts) != 4:
             raise ValueError("Invalid bbox format")
        bounds = {"min_lon": parts[0], "min_lat": parts[1], "max_lon": parts[2], "max_lat": parts[3]}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bbox format. Expected min_lon,min_lat,max_lon,max_lat")

    segments = await service.get_realtime_traffic(bounds)
    return segments

@router.get("/traffic/incidents")
async def get_traffic_incidents():
    """
    Get traffic incidents (dummy)
    """
    return [{"id": 1, "type": "accident", "location": "35.6895,139.6917", "severity": "high"}]

@router.post("/eta/request", response_model=ETAResponse)
async def create_eta_request(request: ETARequestCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new ETA request
    """
    estimated = await service.update_eta(0, {"lat": 0, "lon": 0}) # Initial estimate

    db_request = ETARequest(
        user_id=request.user_id,
        origin=request.origin,
        destination=request.destination,
        mode=request.mode,
        estimated_arrival=estimated,
        requested_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(db_request)
    await db.commit()
    await db.refresh(db_request)
    return db_request

@router.get("/eta/{id}/update")
async def update_eta_endpoint(id: int, lat: float, lon: float, db: AsyncSession = Depends(get_db)):
    """
    Update ETA based on current location
    """
    result = await db.execute(select(ETARequest).where(ETARequest.id == id))
    eta_request = result.scalars().first()
    if not eta_request:
        raise HTTPException(status_code=404, detail="ETA Request not found")

    new_eta = await service.update_eta(id, {"lat": lat, "lon": lon})

    eta_request.estimated_arrival = new_eta
    await db.commit()

    return {"id": id, "estimated_arrival": new_eta}
