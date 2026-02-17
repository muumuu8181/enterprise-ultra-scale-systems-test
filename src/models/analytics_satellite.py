from pydantic import BaseModel
from typing import Dict, Optional
from datetime import date

class ObjectDetection(BaseModel):
    id: str
    scene_id: str
    object_class: str
    count: int
    bbox: Dict
    confidence: float

class CropMonitoring(BaseModel):
    id: str
    parcel_id: str
    date: date
    ndvi: float
    ndwi: float
    crop_type: str
    estimated_yield_t_ha: float
    stress_indicator: str

class DisasterMapping(BaseModel):
    id: str
    event_type: str
    affected_bbox: Dict
    damage_assessment: Dict

# Alias DamageReport to DisasterMapping
DamageReport = DisasterMapping
