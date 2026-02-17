from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import datetime

from src.core.database import get_db
from src.models.mission_models import Satellite, GroundStation, AlertConfiguration, Telemetry, AnomalyLog
from src.services.orbit_propagator import OrbitPropagator
from src.services.anomaly_detector import AnomalyDetector

router = APIRouter(prefix="/mission-ops", tags=["Mission Ops"])

# Pydantic Models
class EmergencyProcedureRequest(BaseModel):
    procedure_type: str

class AnomalyAlertRequest(BaseModel):
    satellite_id: int
    threshold: Dict[str, float]

class HealthResponse(BaseModel):
    satellite_id: int
    status: str
    health_metrics: Dict[str, Any]

class AnomalyResponse(BaseModel):
    alert_created: bool
    satellite_id: int

# Singletons
orbit_propagator = OrbitPropagator()
anomaly_detector = AnomalyDetector()
# Initialize model with dummy data
anomaly_detector.initialize_model()

# Dependency for services
def get_orbit_propagator():
    return orbit_propagator

def get_anomaly_detector():
    return anomaly_detector

@router.get("/missions/{id}/health", response_model=HealthResponse)
async def get_satellite_health(id: int, db: AsyncSession = Depends(get_db)):
    """
    Get satellite health status.
    """
    result = await db.execute(select(Satellite).where(Satellite.id == id))
    satellite = result.scalar_one_or_none()

    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")

    return HealthResponse(
        satellite_id=satellite.id,
        status=satellite.status,
        health_metrics=satellite.health_metrics or {}
    )

@router.post("/missions/{id}/emergency-procedure")
async def execute_emergency_procedure(
    id: int,
    request: EmergencyProcedureRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute emergency procedure.
    """
    result = await db.execute(select(Satellite).where(Satellite.id == id))
    satellite = result.scalar_one_or_none()

    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")

    # Simulate procedure execution
    satellite.status = f"Executing {request.procedure_type}"
    await db.commit()

    return {"status": "procedure initiated", "procedure": request.procedure_type}

@router.get("/ground-stations/coverage")
async def get_ground_station_coverage(
    satellite_id: int,
    ground_station_id: int,
    start_time: Optional[datetime.datetime] = None,
    end_time: Optional[datetime.datetime] = None,
    propagator: OrbitPropagator = Depends(get_orbit_propagator),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate visibility windows for a satellite and ground station.
    """
    sat_result = await db.execute(select(Satellite).where(Satellite.id == satellite_id))
    satellite = sat_result.scalar_one_or_none()

    gs_result = await db.execute(select(GroundStation).where(GroundStation.id == ground_station_id))
    ground_station = gs_result.scalar_one_or_none()

    if not satellite or not ground_station:
        raise HTTPException(status_code=404, detail="Satellite or Ground Station not found")

    if not start_time:
        start_time = datetime.datetime.utcnow()
    if not end_time:
        end_time = start_time + datetime.timedelta(hours=24)

    if not satellite.tle_line1 or not satellite.tle_line2:
        raise HTTPException(status_code=400, detail="Satellite TLE not available")

    windows = propagator.predict_access_windows(
        satellite.tle_line1,
        satellite.tle_line2,
        ground_station.latitude,
        ground_station.longitude,
        ground_station.elevation or 0.0,
        ground_station.min_elevation_angle or 10.0,
        start_time,
        end_time
    )

    return {"windows": windows}

@router.post("/telemetry/anomaly-alerts", response_model=AnomalyResponse)
async def set_anomaly_alerts(
    request: AnomalyAlertRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Set anomaly alert thresholds for a satellite.
    """
    result = await db.execute(select(AlertConfiguration).where(AlertConfiguration.satellite_id == request.satellite_id))
    config = result.scalar_one_or_none()

    if config:
        config.thresholds = request.threshold
    else:
        config = AlertConfiguration(
            satellite_id=request.satellite_id,
            thresholds=request.threshold
        )
        db.add(config)

    await db.commit()
    await db.refresh(config)

    return AnomalyResponse(alert_created=True, satellite_id=request.satellite_id)
