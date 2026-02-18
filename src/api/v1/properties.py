from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from enum import Enum

from src.models.property_models import PropertyType, PropertyStatus
from src.services.property_service import calculate_vacancy_rate

router = APIRouter()

# --- Schemas ---

class PropertyCreate(BaseModel):
    owner_id: int
    address: str
    property_type: PropertyType
    units: int
    amenities: Optional[dict] = None
    status: PropertyStatus = PropertyStatus.AVAILABLE

class PropertyResponse(PropertyCreate):
    id: int

class UnitResponse(BaseModel):
    id: int
    property_id: int
    unit_number: str
    floor: Optional[int] = None
    area_sqm: float
    bedrooms: int
    bathrooms: float
    rent_price: float
    current_tenant_id: Optional[int] = None

class LeaseCreate(BaseModel):
    unit_id: int
    tenant_id: int
    start_date: datetime
    end_date: datetime
    monthly_rent: float
    deposit: float
    terms: Optional[dict] = None

class LeaseResponse(LeaseCreate):
    id: int
    signed_at: Optional[datetime] = None

class PaymentScheduleItem(BaseModel):
    due_date: date
    amount: float
    status: str

# --- Endpoints ---

@router.post("/properties/register", response_model=PropertyResponse)
async def register_property(prop: PropertyCreate):
    """
    Registers a new property.
    """
    # Logic to save to DB would be here
    return PropertyResponse(id=1, **prop.model_dump())

@router.get("/properties/{id}/occupancy")
async def get_occupancy(id: int):
    """
    Returns the occupancy status/rate of a property.
    """
    vacancy_rate = await calculate_vacancy_rate(id)
    return {
        "property_id": id,
        "vacancy_rate": vacancy_rate,
        "occupancy_rate": 1.0 - vacancy_rate
    }

@router.get("/properties/{id}/units", response_model=List[UnitResponse])
async def get_property_units(id: int):
    """
    Lists all units for a property.
    """
    # Placeholder
    return []

@router.get("/units/{id}/lease", response_model=Optional[LeaseResponse])
async def get_unit_lease(id: int):
    """
    Gets the active lease for a specific unit.
    """
    # Placeholder
    return None

@router.post("/leases/create", response_model=LeaseResponse)
async def create_lease(lease: LeaseCreate):
    """
    Creates a new lease agreement.
    """
    return LeaseResponse(id=100, signed_at=datetime.now(), **lease.model_dump())

@router.get("/leases/{id}/payment-schedule", response_model=List[PaymentScheduleItem])
async def get_payment_schedule(id: int):
    """
    Returns the payment schedule for a lease.
    """
    return [
        PaymentScheduleItem(due_date=date.today(), amount=1500.0, status="pending")
    ]
