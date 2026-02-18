from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from geoalchemy2.elements import WKTElement
from geoalchemy2.types import Geography
from src.database import get_db
from src.models.city_models import Sensor, SensorReading, Alert
from src.services.alert_engine import AlertEngine
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/sensors", tags=["sensors"])
alert_engine = AlertEngine()

# Schemas
class SensorCreate(BaseModel):
    device_id: str
    sensor_type: str
    latitude: float
    longitude: float
    metadata_info: Optional[Dict[str, Any]] = None

class SensorReadingCreate(BaseModel):
    timestamp: Optional[datetime] = None
    value: float
    unit: str
    quality_score: float = 1.0

class SensorResponse(BaseModel):
    id: int
    device_id: str
    sensor_type: str
    status: str
    last_seen: datetime
    model_config = ConfigDict(from_attributes=True)

class SensorReadingResponse(BaseModel):
    id: int
    sensor_id: int
    timestamp: datetime
    value: float
    unit: str
    quality_score: float
    model_config = ConfigDict(from_attributes=True)

class AlertResponse(BaseModel):
    id: int
    sensor_id: int
    alert_type: str
    severity: str
    message: str
    triggered_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Endpoints

@router.post("/register", response_model=SensorResponse)
async def register_sensor(sensor: SensorCreate, db: AsyncSession = Depends(get_db)):
    """
    センサーを登録する
    """
    # Create point from lat/lon
    point = f"POINT({sensor.longitude} {sensor.latitude})"

    db_sensor = Sensor(
        device_id=sensor.device_id,
        sensor_type=sensor.sensor_type,
        location=WKTElement(point, srid=4326),
        metadata_info=sensor.metadata_info,
        last_seen=datetime.utcnow()
    )
    db.add(db_sensor)
    try:
        await db.commit()
        await db.refresh(db_sensor)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

    return db_sensor

@router.post("/{sensor_id}/readings")
async def add_readings(sensor_id: int, readings: List[SensorReadingCreate], db: AsyncSession = Depends(get_db)):
    """
    センサーデータを送信 (バッチ対応, 最大100件)
    """
    if len(readings) > 100:
        raise HTTPException(status_code=400, detail="Batch size exceeds limit of 100")

    db_readings = []
    for r in readings:
        reading = SensorReading(
            sensor_id=sensor_id,
            timestamp=r.timestamp or datetime.utcnow(),
            value=r.value,
            unit=r.unit,
            quality_score=r.quality_score
        )
        db_readings.append(reading)

    db.add_all(db_readings)
    await db.commit()

    # アラート評価 (本来はバックグラウンドタスクで行うべき)
    for reading in db_readings:
        await alert_engine.evaluate_rules(reading)

    return {"message": f"Inserted {len(readings)} readings"}

@router.get("/{sensor_id}/readings", response_model=List[SensorReadingResponse])
async def get_readings(
    sensor_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    時系列データ取得
    """
    query = select(SensorReading).where(SensorReading.sensor_id == sensor_id)

    if start_time:
        query = query.where(SensorReading.timestamp >= start_time)
    if end_time:
        query = query.where(SensorReading.timestamp <= end_time)

    query = query.order_by(SensorReading.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    readings = result.scalars().all()
    return readings

@router.get("/nearby", response_model=List[SensorResponse])
async def get_nearby_sensors(
    lat: float,
    lon: float,
    radius: float,
    db: AsyncSession = Depends(get_db)
):
    """
    近傍センサー検索 (PostGIS ST_DWithin使用)
    radiusはメートル単位（投影法に依存するが、ここでは簡易的に度で計算される可能性に注意。
    正確にはGeography型を使うか、ST_DistanceSphereを使うべきだが、
    geoalchemy2のST_DWithinは通常geometry型で動作する。
    SRID 4326の場合、単位は度になるため、メートル変換が必要。
    ここではキャストやGeographyを使用する実装にするか、簡易的に実装する。
    PostGISのST_DWithin(geography(point), geography(point), meters)を使用するのがベスト。
    """
    # WKTElementでPOINTを作成
    point = WKTElement(f"POINT({lon} {lat})", srid=4326)

    # 簡易的にGeometryでキャストして検索（実際はGeography推奨）
    # func.ST_DWithin(Sensor.location, point, radius) # radius in degrees if geometry

    # 正しくはGeographyにキャストしてメートル単位で検索
    query = select(Sensor).where(
        func.ST_DWithin(
            func.ST_SetSRID(Sensor.location, 4326), # Ensure SRID
            point,
            radius, # degrees if geometry, need careful handling.
            # Alternatively use ST_Distance_Sphere or cast to geography
            True # use_spheroid=True (but ST_DWithin signature varies)
        )
    )

    # Using ST_DWithin with geography casting for meters
    # select(Sensor).where(func.ST_DWithin(Sensor.location.cast(Geography), point.cast(Geography), radius))

    # For this implementation, assuming the database setup handles geography or using degrees logic requires conversion.
    # To keep it safe and strictly follow standard PostGIS pattern for meters:
    query = select(Sensor).where(
        func.ST_DWithin(
            func.CAST(Sensor.location, type_=Geography),
            func.CAST(point, type_=Geography),
            radius
        )
    )

    result = await db.execute(query)
    sensors = result.scalars().all()
    return sensors

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(severity: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """
    アラート一覧取得
    """
    query = select(Alert)
    if severity:
        query = query.where(Alert.severity == severity)

    query = query.order_by(Alert.triggered_at.desc())
    result = await db.execute(query)
    alerts = result.scalars().all()
    return alerts
