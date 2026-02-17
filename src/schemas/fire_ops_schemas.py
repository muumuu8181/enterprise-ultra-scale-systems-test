from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from src.models.fire_ops_models import IncidentType, Priority, IncidentStatus, FireStationStatus, ApparatusType, ApparatusStatus

class IncidentBase(BaseModel):
    incident_type: IncidentType
    priority: Priority
    location: Dict[str, Any]

class IncidentCreate(IncidentBase):
    pass

class IncidentResponse(IncidentBase):
    id: int
    reported_at: datetime
    dispatched_at: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    status: IncidentStatus

    model_config = ConfigDict(from_attributes=True)

class ApparatusBase(BaseModel):
    unit_type: ApparatusType
    call_sign: str
    status: ApparatusStatus
    mileage: float
    last_maintenance: datetime

class ApparatusResponse(ApparatusBase):
    id: int
    station_id: int

    model_config = ConfigDict(from_attributes=True)

class FireStationBase(BaseModel):
    name: str
    location: Dict[str, Any]
    district: str
    units: Dict[str, Any]
    personnel_on_duty: int
    status: FireStationStatus

class FireStationResponse(FireStationBase):
    id: int
    apparatus: List[ApparatusResponse] = []

    model_config = ConfigDict(from_attributes=True)

class MaintenanceUpdate(BaseModel):
    last_maintenance: datetime
    mileage: Optional[float] = None
