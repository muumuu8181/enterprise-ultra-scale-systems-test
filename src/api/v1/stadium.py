from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

router = APIRouter()

# Pydantic models
class GateScanRequest(BaseModel):
    ticket_id: str
    gate_id: str
    timestamp: datetime

class RestockRequest(BaseModel):
    item_id: str
    quantity: int

class CrowdDensity(BaseModel):
    section: str
    density_percentage: float
    status: str

# Endpoints

@router.get("/stadiums")
async def get_stadiums(city: Optional[str] = Query(None)):
    """GET /stadiums?city="""
    return {"message": f"List of stadiums in {city}" if city else "List of all stadiums"}

@router.get("/stadiums/{id}/event-calendar")
async def get_event_calendar(id: int):
    """GET /stadiums/{id}/event-calendar"""
    return {"stadium_id": id, "events": []}

@router.get("/events/{id}/attendance-live")
async def get_event_attendance(id: int):
    """GET /events/{id}/attendance-live"""
    return {"event_id": id, "attendance": 0}

@router.post("/events/{id}/gate-scan")
async def gate_scan(id: int, scan: GateScanRequest):
    """POST /events/{id}/gate-scan"""
    return {"event_id": id, "scan_status": "accepted", "details": scan}

@router.get("/concessions/{stadium_id}/sales-live")
async def get_concession_sales(stadium_id: int):
    """GET /concessions/{stadium_id}/sales-live"""
    return {"stadium_id": stadium_id, "total_sales": 0.0, "breakdown": {}}

@router.post("/concessions/{id}/restock")
async def restock_concession(id: int, request: RestockRequest):
    """POST /concessions/{id}/restock"""
    return {"concession_id": id, "restock_status": "completed", "details": request}

@router.get("/security/crowd-density")
async def get_crowd_density(section: Optional[str] = Query(None)):
    """GET /security/crowd-density?section="""
    return {"section": section, "density": "normal"}

@router.get("/analytics/revenue-per-event")
async def get_revenue_per_event():
    """GET /analytics/revenue-per-event"""
    return {"events": []}

@router.get("/parking/{stadium_id}/availability")
async def get_parking_availability(stadium_id: int):
    """GET /parking/{stadium_id}/availability"""
    return {"stadium_id": stadium_id, "available_spots": 1000, "total_spots": 5000}
