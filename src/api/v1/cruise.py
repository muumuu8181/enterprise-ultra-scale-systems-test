from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from src.models.cruise_models import VoyageStatus, CabinType, CabinStatus

router = APIRouter()

# --- Pydantic Models ---

class VoyageBase(BaseModel):
    ship_id: int
    itinerary: Dict[str, Any]
    departure_port: str
    departure_date: datetime
    return_date: datetime
    capacity_passengers: int
    status: VoyageStatus

class VoyageResponse(VoyageBase):
    id: int
    booked_count: int

    class Config:
        from_attributes = True

class CabinBase(BaseModel):
    ship_id: int
    deck: str
    cabin_number: str
    cabin_type: CabinType
    capacity: int
    price_per_night: float
    status: CabinStatus
    amenities: Dict[str, Any]

class CabinResponse(CabinBase):
    id: int

    class Config:
        from_attributes = True

class PortCallResponse(BaseModel):
    id: int
    voyage_id: int
    port_name: str
    country: str
    arrival_time: datetime
    departure_time: datetime
    excursions_available: Dict[str, Any]
    tender_required: bool
    customs_clearance: bool

    class Config:
        from_attributes = True

class ExcursionBookingRequest(BaseModel):
    excursion_id: str
    passenger_id: int

# --- Endpoints ---

@router.get("/voyages", response_model=List[VoyageResponse])
def get_voyages(
    departure_port: Optional[str] = None,
    date_from: Optional[datetime] = None
):
    # TODO: Implement database query
    return []

@router.get("/voyages/{id}/itinerary")
def get_voyage_itinerary(id: int):
    # TODO: Implement logic
    return {"id": id, "itinerary": {}}

@router.get("/cabins/{voyage_id}/available", response_model=List[CabinResponse])
def get_available_cabins(voyage_id: int, type: Optional[CabinType] = None):
    # TODO: Implement logic to find cabins for the ship of the voyage that are available
    return []

@router.post("/cabins/{id}/book")
def book_cabin(id: int):
    # TODO: Implement booking logic
    return {"message": f"Cabin {id} booked"}

@router.get("/ports/{voyage_id}/excursions")
def get_excursions(voyage_id: int):
    # TODO: Implement logic
    return []

@router.post("/excursions/book")
def book_excursion(booking: ExcursionBookingRequest):
    # TODO: Implement logic
    return {"message": "Excursion booked", "details": booking}

@router.get("/ship/{id}/deck-plan")
def get_deck_plan(id: int):
    # TODO: Implement logic
    return {"ship_id": id, "deck_plan": {}}

@router.get("/analytics/occupancy-rate")
def get_occupancy_rate():
    # TODO: Implement logic
    return {"occupancy_rate": 0.0}

@router.post("/muster/checkin/{passenger_id}")
def muster_checkin(passenger_id: int):
    # TODO: Implement logic
    return {"message": f"Passenger {passenger_id} checked in for muster drill"}
