from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from src.models.airport_models import Flight, Gate, FlightStatus, GateStatus, GateAssignment
from src.services.operations_service import assign_gate, optimize_gate_allocation, calculate_on_time_performance

router = APIRouter()

# Dependency placeholder
async def get_db():
    # In a real app, this would yield a database session
    yield

class UpdateGateRequest(BaseModel):
    gate_id: Optional[int] = None

class DelayRequest(BaseModel):
    delay_minutes: int
    reason: Optional[str] = None

@router.get("/flights/departures", response_model=List[dict])  # Simplified response model
async def get_departures(
    terminal: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Flight).where(Flight.origin == "THIS_AIRPORT") # simplified logic
    if terminal:
        # In a real schema, we'd join with Gate to filter by terminal
        # query = query.join(Flight.gate).where(Gate.terminal == terminal)
        pass

    # Mock return for now as we don't have a real DB populated
    return []

@router.get("/flights/arrivals", response_model=List[dict])
async def get_arrivals(db: AsyncSession = Depends(get_db)):
    query = select(Flight).where(Flight.destination == "THIS_AIRPORT")
    # result = await db.execute(query)
    # return result.scalars().all()
    return []

@router.get("/flights/{id}/status", response_model=dict)
async def get_flight_status(
    id: int = Path(..., title="The ID of the flight"),
    db: AsyncSession = Depends(get_db)
):
    # result = await db.get(Flight, id)
    # if not result:
    #     raise HTTPException(status_code=404, detail="Flight not found")
    # return {"status": result.status.value}
    return {"status": "on_time"}

@router.post("/flights/{id}/update-gate", response_model=dict)
async def update_gate(
    id: int = Path(...),
    request: Optional[UpdateGateRequest] = Body(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates the gate for a flight.
    If gate_id is provided, assigns that specific gate.
    Otherwise, triggers automatic assignment.
    """
    if request and request.gate_id:
        # Manual assignment logic (not implemented in service yet)
        return {"message": f"Gate manually updated to {request.gate_id}"}

    # Auto assignment
    try:
        assigned_gate = await assign_gate(id, db)
        if not assigned_gate:
            raise HTTPException(status_code=400, detail="No available gates or flight not found")
        return {"gate_id": assigned_gate.id, "gate_number": assigned_gate.gate_number}
    except Exception as e:
        # Fallback for demo purposes if DB is not configured
        if isinstance(e, HTTPException):
            raise e
        return {"gate_id": 999, "gate_number": "A1 (Demo)"}

@router.post("/flights/{id}/delay", response_model=dict)
async def delay_flight(
    id: int = Path(...),
    request: DelayRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    # Logic to update flight status and time
    # flight = await db.get(Flight, id)
    # if not flight: ...
    # flight.status = FlightStatus.DELAYED
    # flight.actual_dep += timedelta(minutes=request.delay_minutes)
    # await db.commit()
    return {"message": f"Flight delayed by {request.delay_minutes} minutes"}

@router.get("/gates/availability", response_model=List[dict])
async def get_gates_availability(db: AsyncSession = Depends(get_db)):
    # result = await db.execute(select(Gate).where(Gate.status == GateStatus.AVAILABLE))
    # gates = result.scalars().all()
    # return [{"id": g.id, "gate_number": g.gate_number} for g in gates]
    return []
