from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from pydantic import BaseModel
from src.services.infrastructure_service import InfrastructureService
from src.models.infrastructure_models import MaintenancePrediction, TrafficSimResult

router = APIRouter()

def get_service():
    return InfrastructureService()

# Schemas for requests
class InspectionReport(BaseModel):
    inspector_id: str
    condition_score: float
    notes: str

class OptimizationRequest(BaseModel):
    total_budget: float

class ClosureRequest(BaseModel):
    segment_id: int
    duration_hours: int
    start_time: str

# Endpoints

@router.get("/assets/condition-report")
async def get_condition_report(service: InfrastructureService = Depends(get_service)):
    # Mock response
    return {"status": "success", "report_url": "http://example.com/report.pdf"}

@router.post("/assets/{id}/inspection")
async def report_inspection(id: int, report: InspectionReport, service: InfrastructureService = Depends(get_service)):
    # Mock logic
    return {"message": "Inspection recorded", "asset_id": id, "new_score": report.condition_score}

@router.post("/maintenance/schedule-optimize")
async def optimize_schedule(request: OptimizationRequest, service: InfrastructureService = Depends(get_service)):
    schedule = await service.optimize_maintenance_budget(request.total_budget)
    # Return serializable data
    return [
        {
            "id": s.id,
            "asset_id": s.asset_id,
            "maintenance_type": s.maintenance_type,
            "scheduled_date": s.scheduled_date,
            "cost_estimate": s.cost_estimate,
            "priority": s.priority
        } for s in schedule
    ]

@router.get("/maintenance/priority-list")
async def get_priority_list(service: InfrastructureService = Depends(get_service)):
    # Mock priority list
    return [
        {"asset_id": 101, "priority": 1, "reason": "Critical bridge wear"},
        {"asset_id": 205, "priority": 2, "reason": "Pothole density high"}
    ]

@router.get("/traffic/heatmap")
async def get_traffic_heatmap(hour: int = Query(..., ge=0, le=23), service: InfrastructureService = Depends(get_service)):
    # Mock heatmap data
    return {
        "hour": hour,
        "heatmap_data": [
            {"lat": 35.6895, "lon": 139.6917, "intensity": 0.8},
            {"lat": 35.6890, "lon": 139.7000, "intensity": 0.5}
        ]
    }

@router.post("/traffic/simulate-closure", response_model=TrafficSimResult)
async def simulate_closure(closure: ClosureRequest, service: InfrastructureService = Depends(get_service)):
    result = await service.simulate_traffic_impact(closure.model_dump())
    return result
