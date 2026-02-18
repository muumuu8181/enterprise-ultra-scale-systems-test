from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from src.db.session import get_db
from src.models.wearable_models import WearableDevice, HealthMetric, DeviceType, MetricType
from src.services.health_analysis import analyze_hrv, generate_wellness_score, HRVReport
from pydantic import BaseModel, ConfigDict

router = APIRouter()

# Schemas
class DeviceCreate(BaseModel):
    user_id: str
    device_type: DeviceType
    serial: str
    firmware_version: str

class DeviceResponse(BaseModel):
    id: int
    user_id: str
    device_type: DeviceType
    serial: str
    firmware_version: str
    last_sync: datetime
    battery_level: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class MetricResponse(BaseModel):
    id: int
    device_id: int
    metric_type: MetricType
    value: float
    timestamp: datetime
    quality_score: int

    model_config = ConfigDict(from_attributes=True)

class FirmwareUpdate(BaseModel):
    version: str

class BatteryResponse(BaseModel):
    battery_level: Optional[int]

class HealthSummary(BaseModel):
    user_id: str
    wellness_score: float
    hrv_report: HRVReport

# Endpoints

@router.post("/devices/register", response_model=DeviceResponse)
async def register_device(device: DeviceCreate, db: AsyncSession = Depends(get_db)):
    # Check if serial exists
    stmt = select(WearableDevice).where(WearableDevice.serial == device.serial)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Device with this serial already registered")

    new_device = WearableDevice(
        user_id=device.user_id,
        device_type=device.device_type,
        serial=device.serial,
        firmware_version=device.firmware_version
    )
    db.add(new_device)
    await db.commit()
    await db.refresh(new_device)
    return new_device

@router.get("/devices/{id}/sync-data", response_model=List[MetricResponse])
async def sync_data(id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve synced data for a device.
    """
    stmt = select(HealthMetric).where(HealthMetric.device_id == id).order_by(HealthMetric.timestamp.desc())
    result = await db.execute(stmt)
    metrics = result.scalars().all()
    return list(metrics)

@router.post("/devices/{id}/firmware-update", response_model=DeviceResponse)
async def update_firmware(id: int, update: FirmwareUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(WearableDevice).where(WearableDevice.id == id)
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.firmware_version = update.version
    await db.commit()
    await db.refresh(device)
    return device

@router.get("/devices/{id}/battery", response_model=BatteryResponse)
async def get_battery(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(WearableDevice).where(WearableDevice.id == id)
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return BatteryResponse(battery_level=device.battery_level)

@router.get("/users/{id}/health-summary", response_model=HealthSummary)
async def get_health_summary(id: str, db: AsyncSession = Depends(get_db)):
    """
    Get health summary for a user.
    """
    # id here is user_id (string)
    score = await generate_wellness_score(id, db)
    hrv = await analyze_hrv(id, db)

    return HealthSummary(
        user_id=id,
        wellness_score=score,
        hrv_report=hrv
    )

@router.get("/users/{id}/trends", response_model=List[MetricResponse])
async def get_trends(id: str, metric: MetricType, db: AsyncSession = Depends(get_db)):
    """
    Get trends for a specific metric for a user.
    """
    # Join HealthMetric and WearableDevice to filter by user_id
    stmt = select(HealthMetric).join(WearableDevice).where(
        WearableDevice.user_id == id,
        HealthMetric.metric_type == metric
    ).order_by(HealthMetric.timestamp.desc())

    result = await db.execute(stmt)
    metrics = result.scalars().all()
    return list(metrics)
