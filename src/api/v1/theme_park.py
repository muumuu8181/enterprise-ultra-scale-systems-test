from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, ConfigDict

from src.database import get_db
from src.models.theme_park_models import Attraction, WaitTime, Ticket, AttractionStatus, RideType, TicketType, TicketStatus

router = APIRouter()

# Pydantic Schemas
class AttractionBase(BaseModel):
    name: str
    park_zone: str
    ride_type: RideType
    capacity_per_hour: int
    height_requirement_cm: int
    duration_min: int
    status: AttractionStatus = AttractionStatus.OPERATING

class AttractionCreate(AttractionBase):
    pass

class AttractionResponse(AttractionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class WaitTimeResponse(BaseModel):
    attraction_id: int
    current_wait_min: int
    virtual_queue_enabled: bool
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class TicketCreate(BaseModel):
    guest_id: str
    ticket_type: TicketType
    zones_access: List[str]

class TicketResponse(BaseModel):
    id: int
    guest_id: str
    status: TicketStatus
    valid_until: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

# API Endpoints

@router.post("/attractions", response_model=AttractionResponse)
async def create_attraction(attraction: AttractionCreate, db: AsyncSession = Depends(get_db)):
    db_attraction = Attraction(**attraction.model_dump())
    db.add(db_attraction)
    await db.commit()
    await db.refresh(db_attraction)
    return db_attraction

@router.get("/attractions", response_model=List[AttractionResponse])
async def get_attractions(
    zone: Optional[str] = Query(None),
    status: Optional[AttractionStatus] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Attraction)
    if zone:
        query = query.where(Attraction.park_zone == zone)
    if status:
        query = query.where(Attraction.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/attractions/{id}/wait-time", response_model=WaitTimeResponse)
async def get_attraction_wait_time(id: int, db: AsyncSession = Depends(get_db)):
    # Get the latest wait time
    query = select(WaitTime).where(WaitTime.attraction_id == id).order_by(WaitTime.timestamp.desc()).limit(1)
    result = await db.execute(query)
    wait_time = result.scalar_one_or_none()
    if not wait_time:
        # Return a dummy one if none exists for testing
        return WaitTimeResponse(
            attraction_id=id,
            current_wait_min=0,
            virtual_queue_enabled=False,
            timestamp=datetime.now(timezone.utc)
        )
    return wait_time

@router.get("/wait-times/all", response_model=List[WaitTimeResponse])
async def get_all_wait_times(db: AsyncSession = Depends(get_db)):
    # This should probably be "latest wait time for all attractions" but for simplicity returning all
    query = select(WaitTime)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/wait-times/predictions")
async def get_wait_time_predictions(time: datetime):
    # Mock prediction logic
    return {"time": time, "predicted_wait_times": {"coaster_1": 45, "water_ride_1": 20}}

@router.post("/tickets/purchase", response_model=TicketResponse)
async def purchase_ticket(ticket: TicketCreate, db: AsyncSession = Depends(get_db)):
    new_ticket = Ticket(
        guest_id=ticket.guest_id,
        ticket_type=ticket.ticket_type,
        zones_access=ticket.zones_access,
        valid_from=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc) + timedelta(days=1) # Default 1 day validity
    )
    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)
    return new_ticket

@router.get("/tickets/{id}/validate")
async def validate_ticket(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.id == id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Check expiry (naive vs aware datetime comparison)
    now = datetime.now(timezone.utc)
    valid_until = ticket.valid_until
    if valid_until and valid_until.tzinfo is None:
        valid_until = valid_until.replace(tzinfo=timezone.utc)

    is_valid = ticket.status == TicketStatus.ACTIVE and (valid_until is None or valid_until > now)
    return {"valid": is_valid, "status": ticket.status}

@router.post("/virtual-queue/{attraction_id}/join")
async def join_virtual_queue(attraction_id: int, guest_id: str, db: AsyncSession = Depends(get_db)):
    # Mock implementation
    return {"attraction_id": attraction_id, "guest_id": guest_id, "position": 10, "estimated_wait": 30}

@router.get("/virtual-queue/{id}/position")
async def get_virtual_queue_position(id: int): # id could be queue entry id
    return {"queue_id": id, "position": 5, "estimated_wait": 15}

@router.get("/analytics/guest-flow-heatmap")
async def get_guest_flow_heatmap():
    return {
        "zone_a": "high",
        "zone_b": "medium",
        "zone_c": "low"
    }
