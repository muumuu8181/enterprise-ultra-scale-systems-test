from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.db.session import get_db
from src.models.nuclear_models import Reactor, SensorReading, ReactorStatus, SafetySystem, SensorParameter
from src.schemas.nuclear_schemas import (
    ReactorResponse, SensorReadingResponse, SensorReadingCreate,
    Alarm, SafetyMarginReport
)
from src.services.reactor_service import ReactorService

router = APIRouter()

def get_service(db: AsyncSession = Depends(get_db)) -> ReactorService:
    return ReactorService(db)

@router.get("/reactors/{id}/dashboard", response_model=ReactorResponse)
async def get_reactor_dashboard(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Reactor)
        .where(Reactor.id == id)
        .options(selectinload(Reactor.sensor_readings), selectinload(Reactor.safety_systems))
    )
    reactor = result.scalar_one_or_none()
    if not reactor:
        raise HTTPException(status_code=404, detail="Reactor not found")
    return reactor

@router.get("/reactors/{id}/sensors/real-time", response_model=List[SensorReadingResponse])
async def get_real_time_sensors(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SensorReading)
        .where(SensorReading.reactor_id == id)
        .order_by(SensorReading.timestamp.desc())
        .limit(100)
    )
    return result.scalars().all()

@router.post("/reactors/{id}/shutdown", response_model=ReactorResponse)
async def shutdown_reactor(id: int, db: AsyncSession = Depends(get_db)):
    # Trigger SCRAM
    await db.execute(
        update(Reactor)
        .where(Reactor.id == id)
        .values(status=ReactorStatus.SHUTDOWN)
    )
    await db.commit()

    # Return updated reactor
    result = await db.execute(
        select(Reactor)
        .where(Reactor.id == id)
        .options(selectinload(Reactor.sensor_readings), selectinload(Reactor.safety_systems))
    )
    return result.scalar_one()

@router.get("/reactors/{id}/safety-status", response_model=SafetyMarginReport)
async def get_safety_status(id: int, service: ReactorService = Depends(get_service)):
    try:
        return await service.evaluate_safety_margins(id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/plants/{id}/radiation-monitoring", response_model=List[SensorReadingResponse])
async def get_plant_radiation(id: int, db: AsyncSession = Depends(get_db)):
    # Join Reactor and SensorReading to find sensors for reactors in the plant
    result = await db.execute(
        select(SensorReading)
        .join(Reactor)
        .where(Reactor.plant_id == id)
        .where(SensorReading.parameter == SensorParameter.NEUTRON_FLUX)
        .order_by(SensorReading.timestamp.desc())
        .limit(100)
    )
    return result.scalars().all()

@router.post("/alarms/{id}/acknowledge")
async def acknowledge_alarm(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SensorReading).where(SensorReading.id == id))
    reading = result.scalar_one_or_none()

    if not reading:
        raise HTTPException(status_code=404, detail="Alarm not found")

    if not reading.is_alarm:
        raise HTTPException(status_code=400, detail="Reading is not an alarm")

    reading.is_acknowledged = True
    await db.commit()
    return {"message": "Alarm acknowledged"}

# Additional: Endpoint to ingest sensor data
@router.post("/sensors/stream", response_model=List[Alarm])
async def ingest_sensor_stream(
    readings: List[SensorReadingCreate],
    service: ReactorService = Depends(get_service)
):
    return await service.process_sensor_stream(readings)
