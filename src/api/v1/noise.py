from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from geoalchemy2.elements import WKTElement
from geoalchemy2.types import Geography
from src.database import get_db
from src.models.city_models import Sensor
from src.models.noise_models import NoiseReading, NoiseComplaint
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any
from datetime import datetime
import json

router = APIRouter(prefix="/noise", tags=["noise"])

# Schemas
class NoiseReadingCreate(BaseModel):
    db_level: float
    frequency_hz: float

class NoiseReadingResponse(BaseModel):
    id: int
    sensor_id: int
    db_level: float
    frequency_hz: float
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class NoiseComplaintCreate(BaseModel):
    latitude: float
    longitude: float
    db_level: float
    description: str

class NoiseComplaintResponse(BaseModel):
    id: int
    db_level: float
    description: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SensorResponse(BaseModel):
    id: int
    device_id: str
    sensor_type: str
    status: str
    last_seen: datetime
    model_config = ConfigDict(from_attributes=True)

# Endpoints

@router.get("/sensors", response_model=List[SensorResponse])
async def get_noise_sensors(db: AsyncSession = Depends(get_db)):
    """
    騒音センサー一覧を取得
    """
    query = select(Sensor).where(Sensor.sensor_type == "noise")
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/sensors/{sensor_id}/reading", response_model=NoiseReadingResponse)
async def add_noise_reading(
    sensor_id: int,
    reading: NoiseReadingCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    騒音データの登録
    """
    # センサーの存在確認
    sensor = await db.get(Sensor, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    if sensor.sensor_type != "noise":
        raise HTTPException(status_code=400, detail="Sensor is not a noise sensor")

    db_reading = NoiseReading(
        sensor_id=sensor_id,
        db_level=reading.db_level,
        frequency_hz=reading.frequency_hz,
        timestamp=datetime.utcnow()
    )
    db.add(db_reading)
    await db.commit()
    await db.refresh(db_reading)
    return db_reading

@router.get("/heatmap")
async def get_noise_heatmap(
    bounds: Optional[str] = Query(None, description="min_lon,min_lat,max_lon,max_lat"),
    db: AsyncSession = Depends(get_db)
):
    """
    騒音ヒートマップ (GeoJSON FeatureCollection)
    """
    # ST_AsGeoJSONを使ってGeoJSON形式で座標を取得
    stmt = select(
        NoiseReading.db_level,
        func.ST_AsGeoJSON(Sensor.location).label("geojson")
    ).join(Sensor, NoiseReading.sensor_id == Sensor.id)

    # If bounds provided
    if bounds:
        try:
            min_lon, min_lat, max_lon, max_lat = map(float, bounds.split(','))
            stmt = stmt.where(
                func.ST_Within(
                    Sensor.location,
                    func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
                )
            )
        except ValueError:
            pass # Ignore invalid bounds

    res = await db.execute(stmt)
    rows = res.all()

    features = []
    for row in rows:
        geojson_geom = json.loads(row.geojson)
        features.append({
            "type": "Feature",
            "geometry": geojson_geom,
            "properties": {
                "db_level": row.db_level
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }

@router.post("/complaints", response_model=NoiseComplaintResponse)
async def report_complaint(
    complaint: NoiseComplaintCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    騒音苦情の報告
    """
    point = f"POINT({complaint.longitude} {complaint.latitude})"

    db_complaint = NoiseComplaint(
        location=WKTElement(point, srid=4326),
        db_level=complaint.db_level,
        description=complaint.description,
        created_at=datetime.utcnow()
    )
    db.add(db_complaint)
    await db.commit()
    await db.refresh(db_complaint)
    return db_complaint
