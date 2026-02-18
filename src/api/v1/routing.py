from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Union

router = APIRouter(prefix="/routing", tags=["routing"])

class Location(BaseModel):
    lat: float
    lon: float

class DirectionsRequest(BaseModel):
    origin: Location
    destination: Location
    mode: str = Field(default="driving", description="driving, walking, cycling")
    avoid: Optional[List[str]] = Field(default=None, description="List of areas or road types to avoid")

class MatrixRequest(BaseModel):
    origins: List[Location]
    destinations: List[Location]

@router.post("/directions")
async def get_directions(request: DirectionsRequest):
    if request.mode not in ["driving", "walking", "cycling"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be driving, walking, or cycling.")

    # Mock logic
    return {
        "origin": request.origin.model_dump(),
        "destination": request.destination.model_dump(),
        "mode": request.mode,
        "distance_meters": 1200,
        "duration_seconds": 450,
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [request.origin.lon, request.origin.lat],
                [request.destination.lon, request.destination.lat]
            ]
        }
    }

@router.get("/isochrone")
async def get_isochrone(
    origin: str = Query(..., description="Origin coordinates as 'lat,lon'"),
    time_minutes: int = Query(..., description="Time limit in minutes")
):
    try:
        lat_str, lon_str = origin.split(",")
        lat, lon = float(lat_str), float(lon_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid origin format. Use 'lat,lon'")

    # Mock logic
    return {
        "origin": {"lat": lat, "lon": lon},
        "time_minutes": time_minutes,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [lon - 0.01, lat - 0.01],
                [lon + 0.01, lat - 0.01],
                [lon + 0.01, lat + 0.01],
                [lon - 0.01, lat + 0.01],
                [lon - 0.01, lat - 0.01]
            ]]
        }
    }

@router.post("/matrix")
async def get_matrix(request: MatrixRequest):
    # Mock logic
    matrix = []
    for _ in request.origins:
        row = []
        for _ in request.destinations:
            row.append({
                "duration_seconds": 300,
                "distance_meters": 1000
            })
        matrix.append(row)

    return {"matrix": matrix}
