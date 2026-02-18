from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class OrbitType(str, Enum):
    LEO = "LEO"
    MEO = "MEO"
    GEO = "GEO"

class SensorType(str, Enum):
    OPTICAL = "optical"
    SAR = "SAR"
    MULTISPECTRAL = "multispectral"

class ProcessingLevel(str, Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"

class ChangeType(str, Enum):
    DEFORESTATION = "deforestation"
    FLOOD = "flood"
    CONSTRUCTION = "construction"

class Satellite(BaseModel):
    id: str
    name: str
    orbit_type: OrbitType
    sensor_type: SensorType
    resolution_m: float
    revisit_days: int

class ImageScene(BaseModel):
    id: str
    satellite_id: str
    acquisition_time: datetime
    bbox_geojson: dict
    cloud_cover_pct: float
    processing_level: ProcessingLevel
    file_path: str

class ChangeDetection(BaseModel):
    id: str
    scene1_id: str
    scene2_id: str
    change_type: ChangeType
    area_sqkm: float
    confidence: float
