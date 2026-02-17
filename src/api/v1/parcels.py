from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from src.core.database import get_db
from src.models.parcel_models import Parcel, ShipmentEvent, ServiceType, CarrierName
from src.services.carrier_service import CarrierService, ShipmentLabel

router = APIRouter(prefix="/parcels", tags=["parcels"])

class CreateShipmentRequest(BaseModel):
    sender_id: int
    recipient_address: Dict[str, Any]
    weight_kg: float
    dimensions: Dict[str, Any]
    service_type: ServiceType
    carrier: CarrierName

class BatchTrackRequest(BaseModel):
    tracking_numbers: List[str]

class RedirectRequest(BaseModel):
    new_address: Dict[str, Any]

class ShipmentEventResponse(BaseModel):
    event_type: str
    location: str
    timestamp: datetime
    note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

carrier_service = CarrierService()

@router.post("/create-shipment", response_model=ShipmentLabel)
async def create_shipment(
    request: CreateShipmentRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Create Parcel record
    parcel = Parcel(
        sender_id=request.sender_id,
        recipient_address=request.recipient_address,
        weight_kg=request.weight_kg,
        dimensions=request.dimensions,
        service_type=request.service_type,
        tracking_number="PENDING" # Will be updated
    )

    # 2. Call carrier service
    # Note: carrier_service.create_shipment expects a Parcel object
    label = await carrier_service.create_shipment(parcel, request.carrier)

    # 3. Update parcel with tracking number
    parcel.tracking_number = label.tracking_number
    db.add(parcel)
    await db.commit()
    await db.refresh(parcel)

    return label

@router.get("/{tracking}/track", response_model=List[ShipmentEventResponse])
async def track_parcel(tracking: str, carrier: str = "fedex"):
    events = await carrier_service.track_parcel(tracking, carrier)
    return events

@router.get("/{tracking}/events", response_model=List[ShipmentEventResponse])
async def get_parcel_events(tracking: str, db: AsyncSession = Depends(get_db)):
    # Check if parcel exists
    result = await db.execute(select(Parcel).where(Parcel.tracking_number == tracking))
    parcel = result.scalar_one_or_none()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    # Fetch live events
    return await carrier_service.track_parcel(tracking, "fedex")

@router.post("/{tracking}/redirect")
async def redirect_parcel(tracking: str, request: RedirectRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Parcel).where(Parcel.tracking_number == tracking))
    parcel = result.scalar_one_or_none()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    # In a real system, we'd update the dictionary
    updated_address = parcel.recipient_address.copy()
    updated_address.update(request.new_address)
    parcel.recipient_address = updated_address

    await db.commit()
    return {"status": "success", "message": "Redirect requested"}

@router.post("/batch-track")
async def batch_track(request: BatchTrackRequest):
    results = {}
    for tracking in request.tracking_numbers:
        events = await carrier_service.track_parcel(tracking, "fedex")
        # Manually serialize or let FastAPI handle it if we returned a list of models?
        # Since this returns a Dict[str, List[ShipmentEventResponse]], we need to ensure serialization works.
        # We will return list of dicts for simplicity here
        results[tracking] = [
            ShipmentEventResponse.model_validate(e).model_dump() for e in events
        ]
    return results

@router.get("/{id}/label")
async def get_label(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Parcel).where(Parcel.id == id))
    parcel = result.scalar_one_or_none()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    return {"label_url": f"https://api.fedex.com/labels/{parcel.tracking_number}.pdf"}
