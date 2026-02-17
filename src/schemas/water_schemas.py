from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum
from src.models.water_models import PlantType, PlantStatus, SamplePoint, ChemicalType
from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKBElement
from shapely.geometry import mapping

class TreatmentPlantBase(BaseModel):
    name: str
    capacity_mld: float
    plant_type: PlantType
    status: PlantStatus
    serving_population: Optional[int] = None
    location: Optional[Any] = None

    @field_validator('location', mode='before')
    @classmethod
    def serialize_location(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, WKBElement):
             shape = to_shape(v)
             return mapping(shape)
        return v

class TreatmentPlantCreate(TreatmentPlantBase):
    pass

class TreatmentPlantResponse(TreatmentPlantBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class WaterQualitySampleBase(BaseModel):
    plant_id: int
    sample_point: SamplePoint
    ph: Optional[float] = None
    turbidity_ntu: Optional[float] = None
    chlorine_ppm: Optional[float] = None
    tds_ppm: Optional[float] = None
    e_coli_count: Optional[int] = None
    compliant: Optional[bool] = True

class WaterQualitySampleCreate(WaterQualitySampleBase):
    pass

class WaterQualitySampleResponse(WaterQualitySampleBase):
    id: int
    sampled_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ChemicalDosingBase(BaseModel):
    plant_id: int
    chemical: ChemicalType
    dosage_mg_l: Optional[float] = None
    flow_rate: Optional[float] = None
    tank_level_pct: Optional[float] = None
    auto_adjusted: bool = False

class ChemicalDosingCreate(ChemicalDosingBase):
    pass

class ChemicalDosingResponse(ChemicalDosingBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class DashboardResponse(BaseModel):
    plant: TreatmentPlantResponse
    latest_quality: Optional[WaterQualitySampleResponse] = None
    latest_dosing: Optional[ChemicalDosingResponse] = None
    status: PlantStatus
