from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/geocoding", tags=["geocoding"])

class GeocodeRequest(BaseModel):
    address: str

class ReverseGeocodeRequest(BaseModel):
    lat: float
    lon: float

class GeocodeResponse(BaseModel):
    lat: float
    lon: float
    address: str

class POI(BaseModel):
    name: str
    lat: float
    lon: float
    category: str

# Mock data
MOCK_LOCATIONS = {
    "tokyo tower": {"lat": 35.6586, "lon": 139.7454, "address": "Tokyo Tower, Minato, Tokyo"},
    "shibuya crossing": {"lat": 35.6595, "lon": 139.7004, "address": "Shibuya Crossing, Shibuya, Tokyo"},
    "tokyo station": {"lat": 35.6812, "lon": 139.7671, "address": "Tokyo Station, Chiyoda, Tokyo"},
}

MOCK_POIS = [
    POI(name="Tokyo Tower", lat=35.6586, lon=139.7454, category="landmark"),
    POI(name="Shibuya Sky", lat=35.6595, lon=139.7004, category="attraction"),
    POI(name="Ramen Street", lat=35.6812, lon=139.7671, category="food"),
    POI(name="Imperial Palace", lat=35.6852, lon=139.7528, category="landmark"),
]

@router.post("/forward", response_model=GeocodeResponse)
async def forward_geocode(request: GeocodeRequest):
    """
    Forward geocoding: Address to coordinates.
    """
    query = request.address.lower()
    for name, data in MOCK_LOCATIONS.items():
        if name in query:
            return GeocodeResponse(lat=data["lat"], lon=data["lon"], address=data["address"])

    # Return a default mock for unknown addresses
    return GeocodeResponse(lat=35.6895, lon=139.6917, address=request.address)

@router.post("/reverse", response_model=GeocodeResponse)
async def reverse_geocode(request: ReverseGeocodeRequest):
    """
    Reverse geocoding: Coordinates to address.
    """
    min_dist = float('inf')
    closest_addr = "Unknown Location"

    # Simple nearest neighbor search
    for name, data in MOCK_LOCATIONS.items():
        dist = ((data["lat"] - request.lat)**2 + (data["lon"] - request.lon)**2)**0.5
        if dist < min_dist:
            min_dist = dist
            closest_addr = data["address"]

    if min_dist < 0.01: # Approx 1km tolerance
        return GeocodeResponse(lat=request.lat, lon=request.lon, address=closest_addr)

    return GeocodeResponse(lat=request.lat, lon=request.lon, address=f"Location at {request.lat}, {request.lon}")

@router.get("/search", response_model=List[POI])
async def search_poi(q: str = Query(..., min_length=1, description="Search query for POI")):
    """
    POI Search using simulated PostGIS Full Text Search.
    """
    results = []
    query = q.lower()
    for poi in MOCK_POIS:
        if query in poi.name.lower() or query in poi.category.lower():
            results.append(poi)
    return results
