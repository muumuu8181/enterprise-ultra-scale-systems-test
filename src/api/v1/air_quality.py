from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape
from src.database import get_db
from src.models.air_models import AQStation, AQReading, AQAlert, AQAlertRule
from src.services.aqi_calculator import AQICalculator
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/air", tags=["air_quality"])

# --- Schemas ---

class AQStationResponse(BaseModel):
    id: int
    station_id: str
    name: str
    operator: str
    installed_at: datetime
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)

class AQReadingResponse(BaseModel):
    id: int
    station_id: int
    timestamp: datetime
    pm25: Optional[float]
    pm10: Optional[float]
    no2: Optional[float]
    o3: Optional[float]
    co: Optional[float]
    aqi: Optional[int]
    aqi_level: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AQForecastItem(BaseModel):
    time: datetime
    aqi: int
    level: str
    primary_pollutant: str

class AQAlertRuleCreate(BaseModel):
    threshold_aqi: int
    area_polygon: str # WKT format expected (e.g. "POLYGON((...))")

class AQAlertRuleResponse(BaseModel):
    id: int
    threshold_aqi: int
    created_at: datetime
    message: str = "Alert rule created successfully"

# --- Endpoints ---

@router.get("/stations", response_model=List[AQStationResponse])
async def get_stations(db: AsyncSession = Depends(get_db)):
    """
    観測局一覧を取得
    """
    # ST_X, ST_Y using cast to geometry if needed, but simpler to use ST_AsText or just access properties if mapped.
    # Since location is Mapped[Any], we need to query coordinates explicitly or handle WKB.
    # For simplicity, we'll query properties.

    query = select(AQStation)
    result = await db.execute(query)
    stations = result.scalars().all()

    response = []
    for s in stations:
        # location is a WKBElement. strict GeoAlchemy2 usage:
        # shape = to_shape(s.location)
        # lat = shape.y, lon = shape.x
        # But this requires shapely.
        # Alternatively, use DB functions to get coords.

        # Let's use a secondary query or just to_shape if shapely is installed (it usually is with geoalchemy2).
        try:
            shape = to_shape(s.location)
            lat = shape.y
            lon = shape.x
        except Exception:
            lat = 0.0
            lon = 0.0

        response.append(AQStationResponse(
            id=s.id,
            station_id=s.station_id,
            name=s.name,
            operator=s.operator,
            installed_at=s.installed_at,
            latitude=lat,
            longitude=lon
        ))

    return response

@router.get("/stations/{station_id}/current", response_model=AQReadingResponse)
async def get_station_current(station_id: int, db: AsyncSession = Depends(get_db)):
    """
    指定した観測局の現在の測定値を取得
    """
    query = select(AQReading).where(AQReading.station_id == station_id).order_by(AQReading.timestamp.desc()).limit(1)
    result = await db.execute(query)
    reading = result.scalar_one_or_none()

    if not reading:
        raise HTTPException(status_code=404, detail="No readings found for this station")

    # Calculate level if AQI is present
    level = None
    if reading.aqi is not None:
        level = AQICalculator.get_aqi_level(reading.aqi)
    else:
        # Try to calculate on the fly
        aqi, _ = AQICalculator.calculate_aqi(
            pm25=reading.pm25, pm10=reading.pm10, no2=reading.no2, o3=reading.o3, co=reading.co
        )
        if aqi > 0:
            reading.aqi = aqi
            level = AQICalculator.get_aqi_level(aqi)

    # Convert to response
    return AQReadingResponse(
        id=reading.id,
        station_id=reading.station_id,
        timestamp=reading.timestamp,
        pm25=reading.pm25,
        pm10=reading.pm10,
        no2=reading.no2,
        o3=reading.o3,
        co=reading.co,
        aqi=reading.aqi,
        aqi_level=level
    )

@router.get("/forecast", response_model=List[AQForecastItem])
async def get_forecast(lat: float, lon: float):
    """
    指定地点の24時間AQI予測 (モック)
    """
    forecasts = []
    base_time = datetime.utcnow()

    # Simple deterministic mock based on lat/lon to be consistent
    seed = int(lat * 1000 + lon * 1000)
    random.seed(seed)

    base_aqi = random.randint(30, 120)

    for i in range(24):
        time = base_time + timedelta(hours=i)
        # Fluctuate AQI
        hourly_aqi = max(0, base_aqi + random.randint(-20, 20))
        level = AQICalculator.get_aqi_level(hourly_aqi)
        pollutant = random.choice(["PM2.5", "O3", "PM10"])

        forecasts.append(AQForecastItem(
            time=time,
            aqi=hourly_aqi,
            level=level,
            primary_pollutant=pollutant
        ))

    return forecasts

@router.post("/alerts", response_model=AQAlertRuleResponse)
async def create_alert_rule(rule: AQAlertRuleCreate, db: AsyncSession = Depends(get_db)):
    """
    アラート設定を作成 (閾値とエリア)
    """
    try:
        # Validate WKT simply by trying to create WKTElement
        # In a real app, use shapely to validate geometry type
        polygon = WKTElement(rule.area_polygon, srid=4326)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid WKT polygon: {str(e)}")

    new_rule = AQAlertRule(
        threshold_aqi=rule.threshold_aqi,
        area_polygon=polygon,
        created_at=datetime.utcnow()
    )

    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)

    return AQAlertRuleResponse(
        id=new_rule.id,
        threshold_aqi=new_rule.threshold_aqi,
        created_at=new_rule.created_at
    )
