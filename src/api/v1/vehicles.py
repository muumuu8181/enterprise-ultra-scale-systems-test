from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel, ConfigDict
import enum
import calendar

from src.core.database import get_db
from src.models.rental_models import Vehicle, RentalBooking, Insurance, VehicleCategory, VehicleStatus, InsuranceType, BookingStatus
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

# --- Pydantic Schemas ---

class VehicleResponse(BaseModel):
    id: int
    make: str
    model: str
    year: int
    category: VehicleCategory
    daily_rate: float
    status: VehicleStatus
    location: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def serialize_location(loc):
        if loc is None:
            return None
        try:
            shape = to_shape(loc)
            return {"lat": shape.y, "lon": shape.x}
        except Exception:
            return str(loc)

class BookingRequest(BaseModel):
    pickup_date: datetime
    return_date: datetime
    insurance_type: InsuranceType
    renter_id: int

class BookingResponse(BaseModel):
    id: int
    vehicle_id: int
    renter_id: int
    pickup_date: datetime
    return_date: datetime
    total_price: float
    status: BookingStatus
    insurance_type: InsuranceType

    model_config = ConfigDict(from_attributes=True)

class AvailabilityResponse(BaseModel):
    vehicle_id: int
    month: str
    available_days: List[date]

# --- Endpoints ---

@router.get("/", response_model=List[VehicleResponse])
async def get_vehicles(
    category: Optional[VehicleCategory] = None,
    location: Optional[str] = Query(None, description="lat,lon format"),
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    status: Optional[VehicleStatus] = None,
    radius_meters: Optional[float] = Query(5000.0, description="Radius in meters for location search"),
    db: AsyncSession = Depends(get_db)
):
    query = select(Vehicle)

    if category:
        query = query.where(Vehicle.category == category)

    if price_min is not None:
        query = query.where(Vehicle.daily_rate >= price_min)

    if price_max is not None:
        query = query.where(Vehicle.daily_rate <= price_max)

    if status:
        query = query.where(Vehicle.status == status)

    if location:
        try:
            lat, lon = map(float, location.split(','))
            pt = WKTElement(f"POINT({lon} {lat})", srid=4326)
            # Use ST_DWithin if available. Note: usage depends on DB support (PostGIS/SpatiaLite)
            query = query.where(func.ST_DWithin(Vehicle.location, pt, radius_meters))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid location format. Use lat,lon")

    result = await db.execute(query)
    vehicles = result.scalars().all()

    response = []
    for v in vehicles:
        v_dict = {
            "id": v.id,
            "make": v.make,
            "model": v.model,
            "year": v.year,
            "category": v.category,
            "daily_rate": v.daily_rate,
            "status": v.status,
            "location": VehicleResponse.serialize_location(v.location)
        }
        response.append(v_dict)

    return response

@router.get("/{id}", response_model=VehicleResponse)
async def get_vehicle(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vehicle).where(Vehicle.id == id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    v_dict = {
            "id": vehicle.id,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "category": vehicle.category,
            "daily_rate": vehicle.daily_rate,
            "status": vehicle.status,
            "location": VehicleResponse.serialize_location(vehicle.location)
    }
    return v_dict

@router.post("/{id}/book", response_model=BookingResponse)
async def book_vehicle(id: int, booking: BookingRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vehicle).where(Vehicle.id == id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    stmt = select(RentalBooking).where(
        RentalBooking.vehicle_id == id,
        RentalBooking.status != BookingStatus.CANCELLED,
        RentalBooking.pickup_date < booking.return_date,
        RentalBooking.return_date > booking.pickup_date
    )
    result = await db.execute(stmt)
    existing_booking = result.scalar_one_or_none()

    if existing_booking:
        raise HTTPException(status_code=400, detail="Vehicle not available for these dates")

    days = (booking.return_date - booking.pickup_date).days
    if days <= 0:
        raise HTTPException(status_code=400, detail="Invalid dates")

    total_price = days * vehicle.daily_rate

    insurance_cost = 0.0
    deductible = 0.0
    if booking.insurance_type == InsuranceType.BASIC:
        insurance_cost = 15.0 * days
        deductible = 1000.0
    elif booking.insurance_type == InsuranceType.FULL:
        insurance_cost = 30.0 * days
        deductible = 0.0

    total_price += insurance_cost

    new_booking = RentalBooking(
        vehicle_id=id,
        renter_id=booking.renter_id,
        pickup_date=booking.pickup_date,
        return_date=booking.return_date,
        total_price=total_price,
        status=BookingStatus.CONFIRMED,
        pickup_location=vehicle.location
    )
    db.add(new_booking)
    await db.flush()

    new_insurance = Insurance(
        booking_id=new_booking.id,
        type=booking.insurance_type,
        deductible=deductible,
        premium=insurance_cost
    )
    db.add(new_insurance)
    await db.commit()
    await db.refresh(new_booking)

    return {
        "id": new_booking.id,
        "vehicle_id": new_booking.vehicle_id,
        "renter_id": new_booking.renter_id,
        "pickup_date": new_booking.pickup_date,
        "return_date": new_booking.return_date,
        "total_price": new_booking.total_price,
        "status": new_booking.status,
        "insurance_type": booking.insurance_type
    }

@router.get("/{id}/availability", response_model=AvailabilityResponse)
async def check_availability(id: int, month: str = Query(..., description="YYYY-MM"), db: AsyncSession = Depends(get_db)):
    try:
        year, m = map(int, month.split('-'))
        start_date = datetime(year, m, 1)
        if m == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, m + 1, 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    result = await db.execute(select(Vehicle).where(Vehicle.id == id))
    if not result.scalar_one_or_none():
         raise HTTPException(status_code=404, detail="Vehicle not found")

    stmt = select(RentalBooking).where(
        RentalBooking.vehicle_id == id,
        RentalBooking.status != BookingStatus.CANCELLED,
        RentalBooking.return_date > start_date,
        RentalBooking.pickup_date < end_date
    )
    result = await db.execute(stmt)
    bookings = result.scalars().all()

    _, num_days = calendar.monthrange(year, m)
    all_days = [date(year, m, d) for d in range(1, num_days + 1)]
    booked_days = set()

    for b in bookings:
        p = b.pickup_date.date()
        r = b.return_date.date()

        for d in all_days:
            if p <= d < r:
                booked_days.add(d)

    available_days = [d for d in all_days if d not in booked_days]

    return {
        "vehicle_id": id,
        "month": month,
        "available_days": available_days
    }
