from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter()

# Pydantic models
class GeoJSONPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(..., description="[longitude, latitude]")

class EmergencyCallCreate(BaseModel):
    caller_phone: str
    location: GeoJSONPoint
    complaint: str
    triage_level: str

class UnitAssignment(BaseModel):
    call_id: int
    unit_id: int

class PatientHandoff(BaseModel):
    destination_hospital: str
    outcome: str
    handoff_time: datetime

# Endpoints

@router.post("/calls/receive")
async def receive_call(call: EmergencyCallCreate):
    return {"message": "Call received", "call_id": 123, "status": "received", "data": call}

@router.get("/calls/queue")
async def get_call_queue():
    return [{"id": 123, "status": "received", "triage_level": "red", "complaint": "Chest pain"}]

@router.post("/dispatch/assign")
async def assign_unit(assignment: UnitAssignment):
    return {"message": "Unit assigned", "call_id": assignment.call_id, "unit_id": assignment.unit_id}

@router.get("/dispatch/nearest-units")
async def get_nearest_units(lat: float = Query(..., description="Latitude"), lon: float = Query(..., description="Longitude")):
    return [
        {"unit_id": 1, "distance_km": 2.5, "status": "available", "location": {"lat": lat + 0.01, "lon": lon + 0.01}},
        {"unit_id": 2, "distance_km": 5.0, "status": "available", "location": {"lat": lat - 0.02, "lon": lon - 0.02}}
    ]

@router.get("/units/live-map")
async def get_units_live_map():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [139.7, 35.6]},
                "properties": {"unit_id": 1, "status": "available", "call_sign": "AMB-01"}
            }
        ]
    }

@router.get("/units/{id}/status")
async def get_unit_status(id: int):
    return {"unit_id": id, "status": "available", "location": {"type": "Point", "coordinates": [139.7, 35.6]}}

@router.get("/hospitals/capacity")
async def get_hospitals_capacity():
    return [
        {"hospital_id": 1, "name": "Central Hospital", "capacity": 10, "occupied": 8},
        {"hospital_id": 2, "name": "City Medical", "capacity": 20, "occupied": 5}
    ]

@router.post("/patients/{id}/handoff")
async def patient_handoff(id: int, handoff: PatientHandoff):
    return {"message": "Patient handoff recorded", "patient_id": id, "hospital": handoff.destination_hospital}

@router.get("/analytics/response-time-heatmap")
async def get_response_time_heatmap():
    return {
        "grid_size": "1km",
        "data": [
            {"lat": 35.6, "lon": 139.7, "avg_response_time_seconds": 300},
            {"lat": 35.61, "lon": 139.71, "avg_response_time_seconds": 450}
        ]
    }
