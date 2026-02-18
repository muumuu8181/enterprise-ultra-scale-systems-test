from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.database import get_db
from src.models.energy_models import SmartMeter, EnergyReading, DemandResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/energy", tags=["energy"])

# Schemas
class EnergyReadingCreate(BaseModel):
    timestamp: Optional[datetime] = None
    kwh: float
    voltage: float
    current: float
    power_factor: float

class EnergyReadingResponse(BaseModel):
    id: int
    meter_id: int
    timestamp: datetime
    kwh: float
    voltage: float
    current: float
    power_factor: float
    model_config = ConfigDict(from_attributes=True)

class DemandResponseRequest(BaseModel):
    reduction_target_kw: float
    duration_minutes: int

class DemandResponseResponse(BaseModel):
    id: int
    target_reduction: float
    actual_reduction: Optional[float]
    started_at: datetime
    ended_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class ForecastPoint(BaseModel):
    timestamp: datetime
    predicted_kwh: float

# Endpoints

@router.get("/consumption")
async def get_district_consumption(
    district: str,
    db: AsyncSession = Depends(get_db)
):
    """
    地区別消費量を取得
    """
    query = select(func.sum(EnergyReading.kwh)).join(SmartMeter).where(SmartMeter.district == district)
    result = await db.execute(query)
    total_kwh = result.scalar() or 0.0

    return {"district": district, "total_consumption_kwh": total_kwh}

@router.post("/meters/{meter_id}/reading", response_model=EnergyReadingResponse)
async def add_meter_reading(
    meter_id: str,
    reading: EnergyReadingCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    スマートメーター読み取り値を記録
    """
    # Find meter by string ID
    meter_query = select(SmartMeter).where(SmartMeter.meter_id == meter_id)
    result = await db.execute(meter_query)
    meter = result.scalar_one_or_none()

    if not meter:
        raise HTTPException(status_code=404, detail="Smart meter not found")

    new_reading = EnergyReading(
        meter_id=meter.id,
        timestamp=reading.timestamp or datetime.utcnow(),
        kwh=reading.kwh,
        voltage=reading.voltage,
        current=reading.current,
        power_factor=reading.power_factor
    )

    db.add(new_reading)
    await db.commit()
    await db.refresh(new_reading)

    return new_reading

@router.get("/forecast", response_model=List[ForecastPoint])
async def get_energy_forecast(
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
):
    """
    需要予測 (Prophet使用)
    """
    try:
        import pandas as pd
        from prophet import Prophet
    except ImportError:
        logger.warning("Prophet or pandas not installed. Returning mock forecast.")
        # Return a simple mock
        base_time = datetime.utcnow()
        return [
            ForecastPoint(
                timestamp=base_time + timedelta(hours=i),
                predicted_kwh=100.0 + (i * 1.5)
            ) for i in range(hours)
        ]

    # Fetch historical data for training
    # For simplicity, fetching all readings. In production, this would be aggregated.
    query = select(EnergyReading.timestamp, EnergyReading.kwh).order_by(EnergyReading.timestamp)
    result = await db.execute(query)
    rows = result.all()

    if not rows:
        # Not enough data
        base_time = datetime.utcnow()
        return [
            ForecastPoint(
                timestamp=base_time + timedelta(hours=i),
                predicted_kwh=0.0
            ) for i in range(hours)
        ]

    # Prepare DataFrame
    data_list = [{'ds': row[0], 'y': row[1]} for row in rows]
    df = pd.DataFrame(data_list)

    # Prophet logic
    try:
        m = Prophet()
        m.fit(df)
        future = m.make_future_dataframe(periods=hours, freq='H')
        forecast = m.predict(future)

        # Extract future part
        future_forecast = forecast.tail(hours)

        response = []
        for _, row in future_forecast.iterrows():
            response.append(ForecastPoint(
                timestamp=row['ds'],
                predicted_kwh=row['yhat']
            ))
        return response
    except Exception as e:
        logger.error(f"Prophet forecast failed: {e}")
        # Return fallback on error
        base_time = datetime.utcnow()
        return [
            ForecastPoint(
                timestamp=base_time + timedelta(hours=i),
                predicted_kwh=0.0
            ) for i in range(hours)
        ]

@router.post("/demand-response", response_model=DemandResponseResponse)
async def create_demand_response(
    request: DemandResponseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    需要抑制指令を作成
    """
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(minutes=request.duration_minutes)

    dr_event = DemandResponse(
        target_reduction=request.reduction_target_kw,
        started_at=start_time,
        ended_at=end_time
    )

    db.add(dr_event)
    await db.commit()
    await db.refresh(dr_event)

    return dr_event
