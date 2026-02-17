from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional, Dict, Any
from geoalchemy2.elements import WKBElement
from shapely import wkb, to_geojson
import json
from enum import Enum

class DevelopmentStatusEnum(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    UNDER_CONSTRUCTION = "under_construction"
    COMPLETED = "completed"

class ProjectTypeEnum(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    MIXED = "mixed"

class UrbanZoneBase(BaseModel):
    name: str
    zone_type: str
    population_density: float
    avg_income: float
    infrastructure_score: float

class UrbanZoneCreate(UrbanZoneBase):
    pass

class UrbanZoneResponse(UrbanZoneBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class LandParcelBase(BaseModel):
    parcel_id: str
    zoning_code: str
    area_sqm: float
    current_use: str
    allowed_uses: List[str]
    geometry: Any # GeoJSON as dict or WKBElement

class LandParcelCreate(LandParcelBase):
    pass

class LandParcelResponse(LandParcelBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

    @field_validator('geometry', mode='before')
    @classmethod
    def serialize_geometry(cls, v):
        if isinstance(v, WKBElement):
            try:
                # Convert WKBElement to shapely geometry
                shape = wkb.loads(bytes(v.data))
                return json.loads(to_geojson(shape))
            except Exception:
                return str(v)
        elif isinstance(v, str):
             try:
                 # Try hex string
                 shape = wkb.loads(bytes.fromhex(v))
                 return json.loads(to_geojson(shape))
             except:
                 pass
        return v

class DevelopmentProjectBase(BaseModel):
    parcel_id: str
    project_type: ProjectTypeEnum
    units: int
    floors: int
    status: DevelopmentStatusEnum = DevelopmentStatusEnum.PROPOSED

class DevelopmentProjectCreate(DevelopmentProjectBase):
    pass

class DevelopmentProjectResponse(DevelopmentProjectBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ImpactReport(BaseModel):
    project_id: int
    impact_score: float
    notes: str

class OptimizationResult(BaseModel):
    zone_id: int
    optimized_usage: Dict[str, Any]
    score: float
