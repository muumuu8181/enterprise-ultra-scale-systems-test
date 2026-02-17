from fastapi import APIRouter, Depends
from typing import List, Dict
from src.services.ml_service import MLService
from src.models.analytics_satellite import ObjectDetection, CropMonitoring, DisasterMapping, DamageReport
from pydantic import BaseModel
from datetime import date

router = APIRouter()

# Request Models
class ObjectDetectionRequest(BaseModel):
    scene_id: str
    model_name: str

class DisasterAssessRequest(BaseModel):
    event_id: str

# Endpoints
@router.post("/analytics/object-detect", response_model=List[ObjectDetection])
async def detect_objects(request: ObjectDetectionRequest, service: MLService = Depends(MLService)):
    return await service.run_object_detection(request.scene_id, request.model_name)

@router.get("/analytics/crop/{parcel_id}/season", response_model=CropMonitoring)
async def get_crop_season(parcel_id: str, service: MLService = Depends(MLService)):
    return CropMonitoring(
        id="crop_1",
        parcel_id=parcel_id,
        date=date.today(),
        ndvi=0.8,
        ndwi=0.4,
        crop_type="corn",
        estimated_yield_t_ha=10.5,
        stress_indicator="low"
    )

@router.post("/analytics/disaster-assess", response_model=DamageReport)
async def assess_disaster(request: DisasterAssessRequest, service: MLService = Depends(MLService)):
    return await service.assess_disaster_damage(request.event_id)

@router.get("/analytics/time-series")
async def get_time_series(index: str, parcel_id: str, service: MLService = Depends(MLService)):
    return {
        "parcel_id": parcel_id,
        "index": index,
        "data": [
            {"date": "2023-01-01", "value": 0.5},
            {"date": "2023-02-01", "value": 0.6},
        ]
    }
