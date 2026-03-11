from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from src.models.av_testing_models import ScenarioType, TestResult, MetricType

router = APIRouter()

# Pydantic Models

class ScenarioCreate(BaseModel):
    scenario_type: ScenarioType
    description: str
    environment_config: Dict[str, Any]
    expected_behavior: str
    difficulty_level: str
    regulatory_standard: str

class ScenarioResponse(ScenarioCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class RunStartRequest(BaseModel):
    scenario_id: int
    vehicle_id: str

class RunResponse(BaseModel):
    id: int
    scenario_id: int
    vehicle_id: str
    start_time: datetime
    status: str = "started"
    model_config = ConfigDict(from_attributes=True)

class AnnotationRequest(BaseModel):
    annotation: str # Just a placeholder for what annotation might look like
    timestamp: datetime

class MetricSummaryResponse(BaseModel):
    run_id: int
    total_metrics: int
    passed_metrics: int
    failed_metrics: int
    details: List[Dict[str, Any]]

class FleetSafetyScoreResponse(BaseModel):
    score: float
    period: str

class VehicleTestHistoryResponse(BaseModel):
    vehicle_id: str
    total_runs: int
    runs: List[RunResponse]

class DisengagementTrendResponse(BaseModel):
    trend_data: List[Dict[str, Any]]

# Endpoints

@router.get("/scenarios", response_model=List[ScenarioResponse])
async def list_scenarios(
    type_: Optional[ScenarioType] = Query(None, alias="type"),
    difficulty: Optional[str] = Query(None)
):
    # Mock response
    return []

@router.post("/scenarios/create", response_model=ScenarioResponse)
async def create_scenario(scenario: ScenarioCreate):
    # Mock response
    return ScenarioResponse(id=1, **scenario.model_dump())

@router.post("/runs/start", response_model=RunResponse)
async def start_run(request: RunStartRequest):
    # Mock response
    return RunResponse(
        id=123,
        scenario_id=request.scenario_id,
        vehicle_id=request.vehicle_id,
        start_time=datetime.utcnow()
    )

@router.get("/runs/{id}/replay")
async def replay_run(id: int):
    # Mock log replay
    return {"message": f"Replaying run {id}", "log_stream": "http://minio/logs/run_123.log"}

@router.get("/metrics/{run_id}/summary", response_model=MetricSummaryResponse)
async def get_metrics_summary(run_id: int):
    return MetricSummaryResponse(
        run_id=run_id,
        total_metrics=10,
        passed_metrics=8,
        failed_metrics=2,
        details=[]
    )

@router.get("/metrics/fleet-safety-score", response_model=FleetSafetyScoreResponse)
async def get_fleet_safety_score():
    return FleetSafetyScoreResponse(score=95.5, period="last_30_days")

@router.get("/vehicles/{id}/test-history", response_model=VehicleTestHistoryResponse)
async def get_vehicle_history(id: str):
    return VehicleTestHistoryResponse(
        vehicle_id=id,
        total_runs=5,
        runs=[]
    )

@router.get("/analytics/disengagement-trend", response_model=DisengagementTrendResponse)
async def get_disengagement_trend():
    return DisengagementTrendResponse(trend_data=[{"date": "2023-10-01", "count": 2}])

@router.post("/runs/{id}/annotate")
async def annotate_run(id: int, annotation: AnnotationRequest):
    return {"message": "Annotation added", "run_id": id}
