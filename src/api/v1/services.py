from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.services.booking_service import find_available_providers, create_booking
from src.models.petcare_services import ServiceProvider, Booking, DailyReport, ServiceType, BookingStatus

router = APIRouter()

# --- Pydantic Models ---
class ServiceProviderSchema(BaseModel):
    id: int
    name: str
    service_types: List[str]
    rating: float
    verified: bool
    availability: Dict[str, Any]
    location: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class BookingRequest(BaseModel):
    pet_id: int
    provider_id: int
    service_type: str
    scheduled_at: datetime

class BookingResponse(BaseModel):
    id: int
    pet_id: int
    provider_id: int
    service_type: str
    scheduled_at: datetime
    status: str
    price: float

    class Config:
        from_attributes = True

class DailyReportRequest(BaseModel):
    activities: Dict[str, Any]
    meals_given: int
    behavior_notes: str
    photos: List[str]

# --- Endpoints ---

@router.get("/providers/nearby", response_model=List[ServiceProviderSchema])
async def get_nearby_providers(
    lat: float,
    lon: float,
    service: str = "grooming"
):
    """
    Get nearby providers based on location and service type.
    """
    # Assuming find_available_providers returns a list of ServiceProvider objects
    # Note: mocking datetime.now() for the example call
    providers = await find_available_providers(service, datetime.now(), {"lat": lat, "lon": lon})

    # Manually map or rely on Pydantic's from_attributes (ORM mode)
    return [
        ServiceProviderSchema(
            id=p.id,
            name=p.name,
            service_types=p.service_types,
            rating=p.rating,
            verified=p.verified,
            availability=p.availability,
            # In a real app, convert WKBElement to GeoJSON. Here we use a mock.
            location={"type": "Point", "coordinates": [lon, lat]}
        ) for p in providers
    ]

@router.get("/providers/{id}/availability")
async def get_provider_availability(id: int = Path(..., title="The ID of the provider")):
    """
    Get availability for a specific provider.
    """
    # Placeholder logic
    return {"availability": {"monday": "9am-5pm", "tuesday": "9am-5pm"}}

@router.post("/bookings/create", response_model=BookingResponse)
async def create_new_booking(request: BookingRequest):
    """
    Create a new booking.
    """
    booking = await create_booking(
        request.pet_id,
        request.provider_id,
        request.service_type,
        request.scheduled_at
    )

    # Ensure ID is present for response (mocking if service doesn't assign it)
    if not booking.id:
        booking.id = 1  # Mock ID assignment

    return BookingResponse(
        id=booking.id,
        pet_id=booking.pet_id,
        provider_id=booking.provider_id,
        service_type=booking.service_type.value if hasattr(booking.service_type, 'value') else booking.service_type,
        scheduled_at=booking.scheduled_at,
        status=booking.status.value if hasattr(booking.status, 'value') else booking.status,
        price=booking.price
    )

@router.get("/bookings/{id}/status")
async def get_booking_status(id: int):
    """
    Get the status of a booking.
    """
    # Placeholder
    return {"status": "confirmed"}

@router.post("/bookings/{id}/daily-report")
async def create_daily_report(id: int, report: DailyReportRequest):
    """
    Submit a daily report for a booking.
    """
    # Placeholder logic to save report
    return {"message": "Daily report submitted successfully", "booking_id": id}

@router.get("/pets/{id}/activity-history")
async def get_pet_activity_history(id: int):
    """
    Get activity history for a pet.
    """
    # Placeholder
    return [
        {"date": "2023-10-25", "activity": "Morning Walk", "duration_minutes": 30},
        {"date": "2023-10-26", "activity": "Grooming", "notes": " behaved well"}
    ]
