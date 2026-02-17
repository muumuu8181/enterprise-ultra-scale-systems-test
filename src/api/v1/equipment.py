from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from src.services.prediction_service import (
    train_rul_model,
    predict_rul,
    optimize_maintenance_schedule,
    ModelMetrics,
    WorkOrder
)

router = APIRouter()

# --- Request Schemas ---
class EquipmentRegisterRequest(BaseModel):
    name: str
    equipment_type: str
    manufacturer: str
    location: str
    criticality: str

class MaintenanceScheduleRequest(BaseModel):
    equipment_ids: List[int]

# --- Response Schemas ---
class HealthScoreResponse(BaseModel):
    equipment_id: int
    health_score: float
    status: str

class SensorHistoryResponse(BaseModel):
    equipment_id: int
    sensor_type: str
    history: List[dict] # {timestamp, value}

class AtRiskEquipmentResponse(BaseModel):
    equipment_id: int
    risk_level: str
    predicted_failure_date: Optional[datetime]

# --- Endpoints ---

@router.post("/equipment/register")
async def register_equipment(request: EquipmentRegisterRequest):
    # Placeholder: save to DB
    return {"message": "Equipment registered successfully", "id": 123}

@router.get("/equipment/{id}/health-score", response_model=HealthScoreResponse)
async def get_health_score(id: int):
    # Placeholder logic
    return HealthScoreResponse(
        equipment_id=id,
        health_score=85.5,
        status="Good"
    )

@router.get("/equipment/{id}/sensor-history")
async def get_sensor_history(id: int, hours: int = 24):
    # Placeholder logic
    history = []
    start_time = datetime.utcnow() - timedelta(hours=hours)
    for i in range(10):
        history.append({
            "timestamp": start_time + timedelta(hours=i * (hours/10)),
            "value": 100.0 + i
        })

    return {
        "equipment_id": id,
        "sensor_type": "vibration", # simplified
        "history": history
    }

@router.get("/equipment/at-risk", response_model=List[AtRiskEquipmentResponse])
async def get_at_risk_equipment():
    # Placeholder logic
    return [
        AtRiskEquipmentResponse(
            equipment_id=101,
            risk_level="High",
            predicted_failure_date=datetime.utcnow() + timedelta(days=2)
        ),
        AtRiskEquipmentResponse(
            equipment_id=102,
            risk_level="Medium",
            predicted_failure_date=datetime.utcnow() + timedelta(days=15)
        )
    ]

@router.post("/maintenance/schedule-optimal", response_model=List[WorkOrder])
async def schedule_optimal_maintenance(request: MaintenanceScheduleRequest):
    return await optimize_maintenance_schedule(request.equipment_ids)

@router.get("/maintenance/work-orders", response_model=List[WorkOrder])
async def get_work_orders():
    # Placeholder logic
    return await optimize_maintenance_schedule([1, 2, 3]) # Dummy data
