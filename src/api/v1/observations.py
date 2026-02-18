from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.db.session import get_db
from src.services.climate_service import ClimateService, ExtremeEvent, ForecastResult
from src.models.climate_models import ClimateReading

router = APIRouter()

class ReadingCreate(BaseModel):
    station_id: str
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    wind_dir: float
    precipitation: float
    timestamp: Optional[datetime] = None

class ForecastRequest(BaseModel):
    model_id: str
    init_time: datetime = datetime.utcnow()

async def get_climate_service(db: AsyncSession = Depends(get_db)) -> ClimateService:
    return ClimateService(db)

@router.post("/observations/ingest", status_code=201)
async def ingest_observations(
    readings: List[ReadingCreate],
    service: ClimateService = Depends(get_climate_service)
):
    # Logic to save readings
    # For now, just a placeholder or basic save
    # In a real app, this would use service method
    return {"message": f"Ingested {len(readings)} readings"}

@router.get("/observations/stations/{station_id}/latest", response_model=ReadingCreate)
async def get_latest_observation(
    station_id: str,
    service: ClimateService = Depends(get_climate_service)
):
    # Placeholder
    return ReadingCreate(
        station_id=station_id,
        temperature=20.5,
        humidity=60.0,
        pressure=1013.25,
        wind_speed=5.0,
        wind_dir=180.0,
        precipitation=0.0,
        timestamp=datetime.utcnow()
    )

@router.get("/observations/interpolate")
async def interpolate_observations(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    variable: str = Query("temperature", description="Variable to interpolate"),
    service: ClimateService = Depends(get_climate_service)
):
    value = await service.interpolate_spatial(lat, lon, variable)
    return {"latitude": lat, "longitude": lon, "variable": variable, "value": value}

@router.get("/observations/anomalies", response_model=List[ExtremeEvent])
async def get_anomalies(
    service: ClimateService = Depends(get_climate_service)
):
    # Example bbox
    bbox = (-90.0, -180.0, 90.0, 180.0)
    return await service.detect_extreme_events(bbox, threshold=30.0)

@router.post("/models/run-forecast", response_model=ForecastResult)
async def run_forecast(
    request: ForecastRequest,
    service: ClimateService = Depends(get_climate_service)
):
    return await service.run_ensemble_forecast(request.model_id, request.init_time)

@router.get("/models/{model_id}/forecast", response_model=ForecastResult)
async def get_forecast(
    model_id: str,
    hours: int = Query(72, description="Forecast horizon in hours"),
    service: ClimateService = Depends(get_climate_service)
):
    # This might return existing forecast or run new one
    return await service.run_ensemble_forecast(model_id, datetime.utcnow())
