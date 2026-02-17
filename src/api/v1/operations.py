from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from src.database import get_db
from src.models.operations_models import Station, NetworkDisruption, MaintenanceWindow, DisruptionType, MaintenanceWindowType
from src.services.operations_service import recalculate_timetable, allocate_replacement_service, calculate_punctuality_score, BusServicePlan
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter()

# --- Pydantic Schemas ---

class DisruptionReport(BaseModel):
    disruption_type: DisruptionType
    affected_lines: List[str] = Field(default_factory=list)
    start_time: datetime
    estimated_end: Optional[datetime] = None
    passenger_impact: str

class MaintenanceSchedule(BaseModel):
    line_id: str
    window_type: MaintenanceWindowType
    start_time: datetime
    end_time: datetime
    replacement_service: Optional[Dict[str, Any]] = None

# --- Endpoints ---

@router.get("/stations/{id}/departures")
async def get_station_departures(id: int, db: AsyncSession = Depends(get_db)):
    """Get upcoming departures for a station."""
    # Mock data
    return [
        {"train_id": "T101", "destination": "Grand Central", "departure_time": "2023-10-27T10:00:00Z", "platform": 1},
        {"train_id": "T105", "destination": "North Station", "departure_time": "2023-10-27T10:15:00Z", "platform": 2}
    ]

@router.get("/stations/{id}/arrivals")
async def get_station_arrivals(id: int, db: AsyncSession = Depends(get_db)):
    """Get upcoming arrivals for a station."""
    # Mock data
    return [
        {"train_id": "T202", "origin": "South Station", "arrival_time": "2023-10-27T09:55:00Z", "platform": 1},
        {"train_id": "T208", "origin": "West End", "arrival_time": "2023-10-27T10:10:00Z", "platform": 3}
    ]

@router.get("/network/disruptions/live")
async def get_live_disruptions(db: AsyncSession = Depends(get_db)):
    """Get all active network disruptions."""
    # Mock data
    return [
        {
            "id": 1,
            "type": "signal",
            "affected_lines": ["L1", "L2"],
            "start_time": "2023-10-27T08:00:00Z",
            "estimated_end": "2023-10-27T12:00:00Z",
            "passenger_impact": "High"
        }
    ]

@router.post("/disruptions/report")
async def report_disruption(report: DisruptionReport, db: AsyncSession = Depends(get_db)):
    """Report a new network disruption."""
    # Mock: Create disruption object (not saving to DB in this mock)
    new_disruption = NetworkDisruption(
        id=999, # Mock ID
        disruption_type=report.disruption_type,
        affected_lines=report.affected_lines,
        start_time=report.start_time,
        estimated_end=report.estimated_end,
        passenger_impact=report.passenger_impact
    )

    # Recalculate timetable
    await recalculate_timetable(new_disruption)

    # Allocate replacement service
    bus_plan = await allocate_replacement_service(new_disruption.id)

    return {
        "status": "reported",
        "disruption_id": new_disruption.id,
        "replacement_plan": bus_plan
    }

@router.post("/maintenance-windows/schedule")
async def schedule_maintenance(schedule: MaintenanceSchedule, db: AsyncSession = Depends(get_db)):
    """Schedule a maintenance window."""
    # Mock logic
    return {
        "status": "scheduled",
        "maintenance_id": 888,
        "line_id": schedule.line_id,
        "window_type": schedule.window_type
    }

@router.get("/operations/performance-kpis")
async def get_performance_kpis(line_id: Optional[str] = None):
    """Get operational performance KPIs."""
    period = "current_month"
    score = await calculate_punctuality_score(line_id or "all", period)
    return {
        "period": period,
        "line_id": line_id or "all",
        "punctuality_score": score,
        "passenger_satisfaction": 4.2 # Mock
    }
