from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from src.models.nuclear_models import ReactorType, ReactorStatus, SafetySystemType, SafetySystemStatus, SensorParameter

class SensorReadingBase(BaseModel):
    sensor_id: str
    parameter: SensorParameter
    value: float
    is_alarm: bool = False
    timestamp: Optional[datetime] = None

class SensorReadingCreate(SensorReadingBase):
    reactor_id: int

class SensorReadingResponse(SensorReadingBase):
    id: int
    reactor_id: int

    model_config = ConfigDict(from_attributes=True)

class SafetySystemBase(BaseModel):
    system_type: SafetySystemType
    status: SafetySystemStatus
    last_test: Optional[datetime] = None

class SafetySystemResponse(SafetySystemBase):
    id: int
    reactor_id: int

    model_config = ConfigDict(from_attributes=True)

class ReactorBase(BaseModel):
    plant_id: int
    reactor_type: ReactorType
    thermal_power_mw: float
    status: ReactorStatus
    core_temperature: float

class ReactorCreate(ReactorBase):
    pass

class ReactorResponse(ReactorBase):
    id: int
    sensor_readings: List[SensorReadingResponse] = []
    safety_systems: List[SafetySystemResponse] = []

    model_config = ConfigDict(from_attributes=True)

class Alarm(BaseModel):
    sensor_id: str
    parameter: SensorParameter
    current_value: float
    threshold: float
    timestamp: datetime
    message: str

class SafetyMarginReport(BaseModel):
    reactor_id: int
    timestamp: datetime
    core_temp_margin: float
    thermal_power_margin: float
    overall_status: str  # "SAFE", "WARNING", "CRITICAL"
