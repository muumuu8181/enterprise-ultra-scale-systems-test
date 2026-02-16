from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class SensorType(str, Enum):
    TRAFFIC_CAMERA = "traffic_camera"
    TRAFFIC_SIGNAL = "traffic_signal"
    ENVIRONMENT = "environment"

class SignalPhase(str, Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"

class BaseSensorData(BaseModel):
    sensor_id: str
    sensor_type: SensorType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: dict  # {"lat": float, "lon": float}

class TrafficCameraData(BaseSensorData):
    vehicle_count: int
    avg_speed_kmh: float
    congestion_level: str  # "low", "medium", "high"

class TrafficSignalData(BaseSensorData):
    current_phase: SignalPhase
    phase_duration_seconds: int

class EnvironmentData(BaseSensorData):
    temperature: float
    humidity: float
    pm25: float
