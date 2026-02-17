from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_serializer

from src.database import get_db
from src.models.transport_models import TransitVehicle, TransitStop, ArrivalPrediction
from src.services.eta_calculator import ETACalculator

# geoalchemy2 handling
from geoalchemy2.elements import WKBElement, WKTElement
from geoalchemy2.shape import to_shape

router = APIRouter(prefix="/transport", tags=["Public Transport"])
eta_calculator = ETACalculator()

# --- Pydantic Models ---

class TransitVehicleResponse(BaseModel):
    vehicle_id: str
    route_id: str
    operator: str
    speed: float
    heading: float
    updated_at: datetime
    location: Any = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('location')
    def serialize_location(self, value: Any, _info):
        # WKBElementから座標を抽出してDictで返す
        if isinstance(value, (WKBElement, WKTElement)):
            try:
                shape = to_shape(value)
                return {"lat": shape.y, "lon": shape.x}
            except Exception:
                return str(value)
        return value

class VehicleLocationUpdate(BaseModel):
    lat: float
    lon: float
    speed: float
    heading: float

class ArrivalPredictionResponse(BaseModel):
    stop_id: str
    vehicle_id: str
    predicted_arrival: datetime
    confidence: float

    model_config = ConfigDict(from_attributes=True)

class RouteOptimizeResponse(BaseModel):
    summary: Dict[str, Any]
    segments: List[Dict[str, Any]]

# --- Endpoints ---

@router.get("/buses/{route_id}/realtime", response_model=List[TransitVehicleResponse])
async def get_bus_locations(route_id: str, db: AsyncSession = Depends(get_db)):
    """
    指定された路線のバスのリアルタイム位置を取得
    """
    stmt = select(TransitVehicle).where(TransitVehicle.route_id == route_id)
    result = await db.execute(stmt)
    vehicles = result.scalars().all()
    return vehicles

@router.get("/stops/{stop_id}/arrivals", response_model=List[ArrivalPredictionResponse])
async def get_stop_arrivals(stop_id: str, db: AsyncSession = Depends(get_db)):
    """
    バス停の到着予測を取得
    """
    # バス停の存在確認
    stop_stmt = select(TransitStop).where(TransitStop.stop_id == stop_id)
    stop_res = await db.execute(stop_stmt)
    stop = stop_res.scalar_one_or_none()

    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    # 到着予測を取得
    stmt = select(ArrivalPrediction).where(ArrivalPrediction.stop_id == stop_id)
    result = await db.execute(stmt)
    predictions = result.scalars().all()
    return predictions

@router.post("/vehicles/{vehicle_id}/location", response_model=TransitVehicleResponse)
async def update_vehicle_location(
    vehicle_id: str,
    location_data: VehicleLocationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    GPS位置更新
    """
    stmt = select(TransitVehicle).where(TransitVehicle.vehicle_id == vehicle_id)
    result = await db.execute(stmt)
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # GeoAlchemy2のPOINT更新 (SRID=4326)
    # PostGISのPOINTは (lon lat) の順
    point_wkt = f"POINT({location_data.lon} {location_data.lat})"
    vehicle.location = WKTElement(point_wkt, srid=4326)

    vehicle.speed = location_data.speed
    vehicle.heading = location_data.heading
    # updated_atはonupdateで更新される

    await db.commit()
    await db.refresh(vehicle)
    return vehicle

@router.get("/route/optimize", response_model=RouteOptimizeResponse)
async def optimize_route(
    from_loc: str = Query(..., alias="from", description="Comma separated lat,lon"),
    to_loc: str = Query(..., alias="to", description="Comma separated lat,lon")
):
    """
    最適経路 (乗り換え含む)
    ?from=35.68,139.76&to=35.65,139.70
    """
    try:
        from_lat, from_lon = map(float, from_loc.split(','))
        to_lat, to_lon = map(float, to_loc.split(','))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid coordinates format. Use 'lat,lon'")

    result = eta_calculator.optimize_route((from_lat, from_lon), (to_lat, to_lon))
    return result
