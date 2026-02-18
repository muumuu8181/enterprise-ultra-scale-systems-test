from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from src.database import get_db
from src.models.ev_charging import EVCharger, ChargingSession, DemandResponse, ChargerStatus
from src.services import ev_service
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter()

# Helper for UTC now
def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

# Response models
class ChargerResponse(BaseModel):
    id: int
    site_id: int
    status: str
    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    id: int
    cost: float
    kwh_delivered: float
    class Config:
        from_attributes = True

class DemandResponseSchema(BaseModel):
    id: int
    site_id: int
    event_type: str
    period: str
    target_reduction_kw: float
    achieved_kw: float
    class Config:
        from_attributes = True

# Request models
class StartSessionRequest(BaseModel):
    user_id: int
    vehicle_id: int

class ParticipateRequest(BaseModel):
    site_id: int
    event_id: int

@router.get("/chargers/available", response_model=List[ChargerResponse])
async def get_available_chargers(
    location: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(EVCharger).where(EVCharger.status == ChargerStatus.AVAILABLE)
    # Location logic omitted as EVCharger has no location field in prompt
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/chargers/{id}/start-session")
async def start_session(
    id: int,
    request: StartSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    charger = await db.get(EVCharger, id)
    if not charger:
        raise HTTPException(status_code=404, detail="Charger not found")
    if charger.status != ChargerStatus.AVAILABLE:
        raise HTTPException(status_code=400, detail="Charger not available")

    # Optional: Call smart charge service
    # profile = await ev_service.smart_charge_schedule(id, 1.0, utc_now())

    session = ChargingSession(
        charger_id=id,
        user_id=request.user_id,
        vehicle_id=request.vehicle_id,
        started_at=utc_now()
    )
    charger.status = ChargerStatus.CHARGING
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"status": "started", "session_id": session.id}

@router.post("/chargers/{id}/stop-session")
async def stop_session(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    # Find active session
    # Note: This query assumes one active session per charger
    stmt = select(ChargingSession).where(
        ChargingSession.charger_id == id,
        ChargingSession.ended_at == None
    )
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="No active session found for this charger")

    session.ended_at = utc_now()
    session.kwh_delivered = 15.5 # Stub
    session.cost = 7.50 # Stub

    charger = await db.get(EVCharger, id)
    if charger:
        charger.status = ChargerStatus.AVAILABLE

    await db.commit()
    return {"status": "stopped", "cost": session.cost}

@router.get("/sessions/{id}/receipt", response_model=SessionResponse)
async def get_receipt(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    session = await db.get(ChargingSession, id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.get("/demand-response/events", response_model=List[DemandResponseSchema])
async def get_dr_events(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(DemandResponse))
    return result.scalars().all()

@router.post("/demand-response/participate")
async def participate_dr(
    request: ParticipateRequest,
    db: AsyncSession = Depends(get_db)
):
    # Stub implementation
    return {"status": "participating", "event_id": request.event_id}
