from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Tuple, Any
from datetime import datetime, timezone
from src.models.sharing_models import VehicleType, VehicleStatus, StationStatus

router = APIRouter(tags=["sharing"])

# Schemas
class GeoJSONPoint(BaseModel):
    type: Literal['Point'] = 'Point'
    coordinates: Tuple[float, float] = Field(..., description="[longitude, latitude]")

class VehicleResponse(BaseModel):
    id: int
    vehicle_type: VehicleType
    serial_number: str
    battery_level_pct: float
    location: GeoJSONPoint
    status: VehicleStatus
    last_maintained: datetime

class RideStartRequest(BaseModel):
    vehicle_id: int
    user_id: int
    start_location: GeoJSONPoint

class RideResponse(BaseModel):
    id: int
    user_id: int
    vehicle_id: int
    start_time: datetime
    start_location: GeoJSONPoint
    status: str = "active"

class RideEndRequest(BaseModel):
    end_location: GeoJSONPoint
    # These might be calculated by server, but for now we accept them or just return them
    payment_method_id: Optional[str] = None

class RideEndResponse(BaseModel):
    id: int
    end_time: datetime
    distance_km: float
    calories_burned: float
    fare: float
    payment_id: Optional[str]

class StationResponse(BaseModel):
    id: int
    name: str
    location: GeoJSONPoint
    capacity: int
    available_vehicles: int
    available_docks: int
    status: StationStatus
    zone: Optional[str]

class ReportIssueRequest(BaseModel):
    issue_description: str

# Endpoints

@router.get("/vehicles/nearby", response_model=List[VehicleResponse])
async def get_nearby_vehicles(
    lat: float,
    lon: float,
    type: Optional[VehicleType] = None
):
    """
    Get nearby vehicles based on latitude and longitude.
    """
    # Mock response
    return []

@router.post("/vehicles/{id}/unlock")
async def unlock_vehicle(id: int):
    """
    Unlock a vehicle for a ride.
    """
    return {"message": "Vehicle unlocked", "vehicle_id": id, "status": "rented"}

@router.post("/rides/start", response_model=RideResponse)
async def start_ride(ride_request: RideStartRequest):
    """
    Start a new ride.
    """
    return RideResponse(
        id=1,
        user_id=ride_request.user_id,
        vehicle_id=ride_request.vehicle_id,
        start_time=datetime.now(timezone.utc),
        start_location=ride_request.start_location
    )

@router.post("/rides/{id}/end", response_model=RideEndResponse)
async def end_ride(id: int, end_request: RideEndRequest):
    """
    End an ongoing ride.
    """
    # Mock calculation
    return RideEndResponse(
        id=id,
        end_time=datetime.now(timezone.utc),
        distance_km=2.5,
        calories_burned=50.0,
        fare=500.0,
        payment_id="pay_12345"
    )

@router.get("/stations", response_model=List[StationResponse])
async def get_stations(zone: Optional[str] = None):
    """
    List stations, optionally filtered by zone.
    """
    return []

@router.get("/stations/{id}/availability")
async def get_station_availability(id: int):
    """
    Get availability of a specific station.
    """
    return {"station_id": id, "available_vehicles": 5, "available_docks": 10}

@router.get("/rides/history")
async def get_ride_history(user_id: int):
    """
    Get ride history for a user.
    """
    return []

@router.get("/analytics/heatmap")
async def get_heatmap(period: str = "24h"):
    """
    Get heatmap data for analytics.
    """
    return {"period": period, "data": []}

@router.post("/vehicles/{id}/report-issue")
async def report_issue(id: int, report: ReportIssueRequest):
    """
    Report an issue with a vehicle.
    """
    return {"message": "Issue reported", "vehicle_id": id}
