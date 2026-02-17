from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import List, Optional

from src.models.v2x_models import EmergencyVehicle, PreemptionRequest
from src.services.signal_preemption import SignalPreemptionService
from src.services.v2x_message_handler import V2XMessageHandler
from src.services.pki_manager import PKIManager

# Mock get_db dependency (similar to v2x_messages.py)
async def get_db():
    yield None

router = APIRouter(prefix="/emergency", tags=["emergency"])

# Dependency Injection
# In a real app, these would be injected via FastAPI dependencies
pki_manager = PKIManager()
message_handler = V2XMessageHandler(pki_manager)
preemption_service = SignalPreemptionService(message_handler)

@router.post("/vehicles/register")
async def register_vehicle(
    vehicle_id: str = Body(..., embed=True),
    vehicle_type: str = Body(..., embed=True, alias="type", pattern="^(ambulance|fire|police)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    緊急車両を登録する。
    """
    if not db:
        # Mock behavior
        return {"vehicle_id": vehicle_id, "type": vehicle_type, "status": "registered (mock)"}

    # Check if exists
    stmt = select(EmergencyVehicle).where(EmergencyVehicle.vehicle_id == vehicle_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        existing.type = vehicle_type
        existing.registered_at = datetime.now(timezone.utc)
    else:
        new_vehicle = EmergencyVehicle(
            vehicle_id=vehicle_id,
            type=vehicle_type,
            registered_at=datetime.now(timezone.utc)
        )
        db.add(new_vehicle)

    await db.commit()
    return {"vehicle_id": vehicle_id, "type": vehicle_type, "status": "registered"}

@router.post("/preemption/request")
async def request_preemption(
    vehicle_id: str = Body(..., embed=True),
    route: dict = Body(..., embed=True),
    eta: float = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    """
    信号優先制御を要求する。
    """
    # preemption_service.receive_preemption_request の引数順序: vehicle_id, route, eta, db
    request_id = await preemption_service.receive_preemption_request(vehicle_id, route, eta, db)
    return {"request_id": request_id, "status": "accepted"}

@router.get("/preemption/{request_id}/status")
async def get_preemption_status(
    request_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    優先制御要求のステータスを確認する。
    """
    if not db:
        return {"request_id": request_id, "status": "granted (mock)"}

    stmt = select(PreemptionRequest).where(PreemptionRequest.request_id == request_id)
    result = await db.execute(stmt)
    request = result.scalar_one_or_none()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    return {"request_id": request_id, "status": request.status}

@router.post("/clearance/broadcast")
async def broadcast_clearance(
    location: dict = Body(..., embed=True, description="{'lat': float, 'lon': float}"),
    radius: float = Body(500.0, embed=True),
    message: str = Body("Emergency Vehicle Approaching. Please clear the way.", embed=True),
    db: AsyncSession = Depends(get_db)
):
    """
    進路確保のためのブロードキャストを行う。
    """
    lat = location.get("lat")
    lon = location.get("lon")

    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Invalid location format")

    payload = {
        "type": "EMERGENCY_CLEARANCE",
        "message": message,
        "location": location,
        "timestamp": str(datetime.now(timezone.utc))
    }

    # V2XMessageHandler.broadcast_to_nearby_vehicles の引数: message, sender_lat, sender_lon, radius_m
    await message_handler.broadcast_to_nearby_vehicles(payload, lat, lon, radius_m=radius)

    return {"status": "broadcast_sent", "target_radius": radius}
