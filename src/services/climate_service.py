from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.climate_models import ClimateModel, ClimateReading, WeatherStation

class ExtremeEvent(BaseModel):
    event_type: str
    severity: str
    location: dict
    timestamp: datetime
    description: str

class ForecastResult(BaseModel):
    model_id: str
    forecast_time: datetime
    predictions: dict
    confidence: float

class ClimateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def interpolate_spatial(self, lat: float, lon: float, variable: str) -> float:
        """
        Interpolates the value of a variable at a given location based on nearby stations.
        """
        allowed_variables = {"temperature", "humidity", "pressure", "wind_speed", "wind_dir", "precipitation"}
        if variable not in allowed_variables:
            raise ValueError(f"Variable '{variable}' is not supported. Allowed: {allowed_variables}")

        # Placeholder logic: average of all readings for that variable
        # In a real implementation, this would query nearby stations and use IDW or Kriging
        stmt = select(ClimateReading).limit(10)
        result = await self.db.execute(stmt)
        readings = result.scalars().all()

        values = [getattr(r, variable) for r in readings if getattr(r, variable) is not None]
        if not values:
            return 0.0

        return sum(values) / len(values)

    async def detect_extreme_events(self, region_bbox: tuple[float, float, float, float], threshold: float) -> List[ExtremeEvent]:
        """
        Detects extreme weather events within a bounding box.
        region_bbox: (min_lat, min_lon, max_lat, max_lon)
        """
        # Placeholder logic
        return [
            ExtremeEvent(
                event_type="Heatwave",
                severity="High",
                location={"lat": (region_bbox[0] + region_bbox[2])/2, "lon": (region_bbox[1] + region_bbox[3])/2},
                timestamp=datetime.utcnow(),
                description=f"Temperature exceeded threshold {threshold}"
            )
        ]

    async def run_ensemble_forecast(self, model_id: str, init_time: datetime) -> ForecastResult:
        """
        Runs an ensemble forecast for a given model.
        """
        # Placeholder logic
        return ForecastResult(
            model_id=model_id,
            forecast_time=init_time,
            predictions={"temperature": 25.0, "precipitation": 0.0},
            confidence=0.85
        )
