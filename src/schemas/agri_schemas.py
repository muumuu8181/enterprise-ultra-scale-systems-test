from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict, List
from datetime import date, datetime
from src.models.agri_models import IrrigationType, SensorType, SensorStatus, PrescriptionType, PrescriptionStatus

class FieldBase(BaseModel):
    farm_id: str
    name: str
    location: Dict[str, Any] # GeoJSON
    area_hectares: float
    crop_type: str
    soil_type: str
    irrigation_type: IrrigationType
    planting_date: date
    expected_harvest: date

class FieldCreate(FieldBase):
    pass

class FieldResponse(FieldBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class SensorNodeBase(BaseModel):
    field_id: int
    sensor_type: SensorType
    location: Dict[str, Any] # GeoJSON
    battery_pct: float
    last_reading_at: datetime
    status: SensorStatus

class SensorNodeCreate(SensorNodeBase):
    pass

class SensorNodeResponse(SensorNodeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CropPrescriptionBase(BaseModel):
    field_id: int
    prescription_type: PrescriptionType
    product: str
    quantity: float
    application_method: str
    scheduled_date: date
    applied_date: Optional[date] = None
    status: PrescriptionStatus

class CropPrescriptionCreate(CropPrescriptionBase):
    pass

class CropPrescriptionResponse(CropPrescriptionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class HealthDashboard(BaseModel):
    field_id: int
    health_score: float
    alerts: List[str]

class YieldPrediction(BaseModel):
    field_id: int
    predicted_yield: float
    confidence: float

class WeatherForecast(BaseModel):
    field_id: int
    date: date
    temperature: float
    precipitation: float
    humidity: float
