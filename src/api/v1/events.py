from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict
from src.database import get_db
from src.models.event_models import Event, Registration, Venue, EventType, EventStatus

router = APIRouter(tags=["events"])

# --- Schemas ---
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: EventType
    start_date: datetime
    end_date: datetime
    capacity: int
    ticket_types: dict
    status: EventStatus = EventStatus.DRAFT
    venue_id: Optional[int] = None

class EventCreate(EventBase):
    organizer_id: int

class EventResponse(EventBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class RegistrationCreate(BaseModel):
    event_id: int
    attendee_id: int
    ticket_type: str
    amount_paid: float
    dietary_preference: Optional[str] = None

class RegistrationResponse(RegistrationCreate):
    id: int
    registration_date: datetime
    check_in_time: Optional[datetime] = None
    badge_printed: bool
    model_config = ConfigDict(from_attributes=True)

class VenueBase(BaseModel):
    name: str
    address: str
    capacity: int
    facilities: dict
    hourly_rate: float
    availability_calendar: dict
    contact_email: str

class VenueCreate(VenueBase):
    pass

class VenueResponse(VenueBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class VenueBookingRequest(BaseModel):
    venue_id: int
    event_id: int

# --- Endpoints ---

@router.get("/events", response_model=List[EventResponse])
async def list_events(
    type: Optional[EventType] = Query(None),
    date_from: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Event)
    if type:
        query = query.where(Event.event_type == type)
    if date_from:
        query = query.where(Event.start_date >= date_from)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/events/create", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    new_event = Event(**event.model_dump())
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    return new_event

@router.post("/registrations/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_attendee(registration: RegistrationCreate, db: AsyncSession = Depends(get_db)):
    new_reg = Registration(**registration.model_dump())
    db.add(new_reg)
    await db.commit()
    await db.refresh(new_reg)
    return new_reg

@router.get("/registrations/{event_id}/attendees", response_model=List[RegistrationResponse])
async def get_attendees(event_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Registration).where(Registration.event_id == event_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/check-in/{registration_id}", response_model=RegistrationResponse)
async def check_in(registration_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Registration).where(Registration.id == registration_id)
    result = await db.execute(query)
    reg = result.scalar_one_or_none()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")

    reg.check_in_time = datetime.now(timezone.utc)
    reg.badge_printed = True
    await db.commit()
    await db.refresh(reg)
    return reg

@router.get("/events/{id}/dashboard")
async def get_event_dashboard(id: int, db: AsyncSession = Depends(get_db)):
    event_query = select(Event).where(Event.id == id)
    event_result = await db.execute(event_query)
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    reg_query = select(func.count(Registration.id)).where(Registration.event_id == id)
    reg_count = await db.execute(reg_query)
    total_registrations = reg_count.scalar()

    checkin_query = select(func.count(Registration.id)).where(Registration.event_id == id, Registration.check_in_time != None)
    checkin_count = await db.execute(checkin_query)
    total_checkins = checkin_count.scalar()

    return {
        "event": event.title,
        "total_registrations": total_registrations,
        "total_checkins": total_checkins,
        "occupancy_rate": (total_registrations / event.capacity) if event.capacity > 0 else 0
    }

@router.get("/venues/search", response_model=List[VenueResponse])
async def search_venues(
    capacity: Optional[int] = Query(None),
    date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Venue)
    if capacity:
        query = query.where(Venue.capacity >= capacity)

    result = await db.execute(query)
    venues = result.scalars().all()

    if date:
        date_str = date.date().isoformat()
        # Filter out venues that are booked on this date
        available_venues = []
        for v in venues:
            booked_dates = v.availability_calendar.get("booked_dates", [])
            if date_str not in booked_dates:
                available_venues.append(v)
        return available_venues

    return venues

@router.post("/venues/book")
async def book_venue(booking: VenueBookingRequest, db: AsyncSession = Depends(get_db)):
    event_q = select(Event).where(Event.id == booking.event_id)
    venue_q = select(Venue).where(Venue.id == booking.venue_id)

    event = (await db.execute(event_q)).scalar_one_or_none()
    venue = (await db.execute(venue_q)).scalar_one_or_none()

    if not event or not venue:
        raise HTTPException(status_code=404, detail="Event or Venue not found")

    # Check availability
    event_date_str = event.start_date.date().isoformat()
    booked_dates = venue.availability_calendar.get("booked_dates", [])
    if event_date_str in booked_dates:
        raise HTTPException(status_code=400, detail="Venue not available on this date")

    event.venue_id = venue.id

    # Update availability calendar
    new_calendar = venue.availability_calendar.copy()
    if "booked_dates" not in new_calendar:
        new_calendar["booked_dates"] = []
    new_calendar["booked_dates"].append(event_date_str)
    venue.availability_calendar = new_calendar

    await db.commit()
    return {"message": "Venue booked successfully"}

@router.get("/analytics/attendance-rate")
async def get_attendance_rate(db: AsyncSession = Depends(get_db)):
    total_regs = await db.execute(select(func.count(Registration.id)))
    total_checkins = await db.execute(select(func.count(Registration.id)).where(Registration.check_in_time != None))

    tr = total_regs.scalar() or 0
    tc = total_checkins.scalar() or 0

    return {
        "attendance_rate": (tc / tr) if tr > 0 else 0,
        "total_registrations": tr,
        "total_checkins": tc
    }

@router.post("/venues/create", response_model=VenueResponse, status_code=status.HTTP_201_CREATED)
async def create_venue(venue: VenueCreate, db: AsyncSession = Depends(get_db)):
    new_venue = Venue(**venue.model_dump())
    db.add(new_venue)
    await db.commit()
    await db.refresh(new_venue)
    return new_venue
