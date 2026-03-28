from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from src.models.pipeline_models import PipelineType, SensorType, IncidentType, Severity, ResponseStatus

router = APIRouter()

# Pydantic Models
class PipelineBase(BaseModel):
    name: str
    pipeline_type: PipelineType
    length_km: float
    diameter_inches: float
    max_pressure_psi: float
    start_location: str
    end_location: str
    commissioned_date: datetime

class PipelineResponse(PipelineBase):
    id: int
    class Config:
        from_attributes = True

class SensorReadingResponse(BaseModel):
    id: int
    pipeline_id: int
    sensor_type: SensorType
    value: float
    unit: str
    location_km: float
    reading_at: datetime
    anomaly_detected: bool
    class Config:
        from_attributes = True

class IncidentCreate(BaseModel):
    pipeline_id: int
    incident_type: IncidentType
    severity: Severity
    location_km: float
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class IncidentResponse(IncidentCreate):
    id: int
    response_status: ResponseStatus
    class Config:
        from_attributes = True

class InspectionSchedule(BaseModel):
    pipeline_id: int
    scheduled_date: datetime
    inspector_name: str
    notes: Optional[str] = None

# Endpoints

@router.get("/pipelines", response_model=List[PipelineResponse])
async def get_pipelines(type: Optional[PipelineType] = Query(None)):
    """
    Get a list of pipelines, optionally filtered by type.
    """
    return []

@router.get("/pipelines/{id}/status")
async def get_pipeline_status(id: int):
    """
    Get the operational status of a specific pipeline.
    """
    return {"pipeline_id": id, "status": "operational", "flow_rate": 1000.0, "pressure": 500.0}

@router.get("/sensors/{pipeline_id}/live", response_model=List[SensorReadingResponse])
async def get_live_sensors(pipeline_id: int):
    """
    Get live sensor readings for a pipeline.
    """
    return []

@router.get("/sensors/{pipeline_id}/anomalies", response_model=List[SensorReadingResponse])
async def get_sensor_anomalies(pipeline_id: int):
    """
    Get recent anomalous sensor readings for a pipeline.
    """
    return []

@router.post("/incidents/report", response_model=IncidentResponse)
async def report_incident(incident: IncidentCreate):
    """
    Report a new incident.
    """
    return IncidentResponse(
        id=1,
        response_status=ResponseStatus.DETECTED,
        **incident.model_dump()
    )

@router.get("/incidents/active", response_model=List[IncidentResponse])
async def get_active_incidents():
    """
    Get all currently active incidents.
    """
    return []

@router.get("/maintenance/{pipeline_id}/pig-runs")
async def get_pig_runs(pipeline_id: int):
    """
    Get history of pig (Pipeline Inspection Gauge) runs.
    """
    return [
        {"id": 101, "pipeline_id": pipeline_id, "date": datetime.now(timezone.utc), "status": "completed", "issues_found": 0}
    ]

@router.post("/maintenance/schedule-inspection")
async def schedule_inspection(schedule: InspectionSchedule):
    """
    Schedule a maintenance inspection.
    """
    return {"message": "Inspection scheduled", "schedule_id": 123, "details": schedule}

@router.get("/analytics/throughput")
async def get_throughput(period: str = Query(..., description="Time period for analysis (e.g. '24h', '7d')")):
    """
    Get throughput analytics for the specified period.
    """
    return {"period": period, "total_throughput_barrels": 50000.0, "average_flow_rate_bph": 2083.3}
