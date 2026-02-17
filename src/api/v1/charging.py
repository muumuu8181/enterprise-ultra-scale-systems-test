from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

router = APIRouter()

# Pydantic models for request/response bodies
class Station(BaseModel):
    id: int
    name: str
    location: dict
    status: str

class Charger(BaseModel):
    id: int
    status: str
    power_kw: float

class SessionStartRequest(BaseModel):
    charger_id: int
    user_id: str
    vehicle_id: str
    payment_method: str

class Session(BaseModel):
    id: int
    charger_id: int
    user_id: str
    status: str
    start_time: datetime

class FaultReport(BaseModel):
    reason: str
    description: Optional[str] = None

@router.get("/stations/nearby", response_model=List[Station])
async def get_nearby_stations(lat: float, lon: float, connector: Optional[str] = None):
    # Mock implementation
    return [
        {"id": 1, "name": "Station A", "location": {"lat": lat, "lon": lon}, "status": "open"}
    ]

@router.get("/stations/{station_id}/availability")
async def get_station_availability(station_id: int):
    # Mock implementation
    return {"station_id": station_id, "available_chargers": 5, "total_chargers": 10}

@router.post("/sessions/start", response_model=Session)
async def start_session(request: SessionStartRequest):
    # Mock implementation
    return {
        "id": 123,
        "charger_id": request.charger_id,
        "user_id": request.user_id,
        "status": "active",
        "start_time": datetime.now(timezone.utc)
    }

@router.post("/sessions/{session_id}/stop")
async def stop_session(session_id: int):
    # Mock implementation
    return {"session_id": session_id, "status": "stopped", "end_time": datetime.now(timezone.utc), "cost": 15.50}

@router.get("/sessions/history")
async def get_session_history(user_id: str):
    # Mock implementation
    return [
        {"id": 101, "date": "2023-10-01", "kwh": 25.5, "cost": 12.00},
        {"id": 102, "date": "2023-10-05", "kwh": 30.0, "cost": 14.50}
    ]

@router.get("/sessions/{session_id}/live-status")
async def get_session_live_status(session_id: int):
    # Mock implementation
    return {"session_id": session_id, "current_power_kw": 50.0, "energy_delivered_kwh": 10.5, "soc": 45}

@router.get("/analytics/utilization")
async def get_station_utilization(station_id: Optional[int] = None):
    # Mock implementation
    return {"station_id": station_id, "utilization_rate": 0.75}

@router.get("/analytics/revenue")
async def get_revenue_analytics(period: str = Query(..., description="daily, weekly, monthly")):
    # Mock implementation
    return {"period": period, "total_revenue": 5000.00}

@router.post("/chargers/{charger_id}/report-fault")
async def report_charger_fault(charger_id: int, report: FaultReport):
    # Mock implementation
    return {"charger_id": charger_id, "status": "fault_reported", "ticket_id": 999}
