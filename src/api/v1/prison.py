from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict

from src.database import get_db
from src.models.prison_models import Inmate, Cell, Incident, SecurityLevel, InmateStatus, CellStatus, IncidentType, IncidentStatus

router = APIRouter()

# Schemas
class InmateBase(BaseModel):
    inmate_number: str
    name: str
    dob: date
    sentence_start: date
    sentence_end: Optional[date] = None
    offense_category: str
    security_level: SecurityLevel
    status: InmateStatus = InmateStatus.INCARCERATED

class InmateCreate(InmateBase):
    pass

class InmateResponse(InmateBase):
    id: int
    cell_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class CellBase(BaseModel):
    block_id: str
    cell_number: str
    capacity: int
    security_level: SecurityLevel
    status: CellStatus = CellStatus.VACANT

class CellCreate(CellBase):
    pass

class CellResponse(CellBase):
    id: int
    current_occupancy: int
    last_inspection: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class IncidentBase(BaseModel):
    incident_type: IncidentType
    severity: str
    location: str
    investigating_officer: str
    status: IncidentStatus = IncidentStatus.REPORTED

class IncidentCreate(IncidentBase):
    inmate_id: int

class IncidentResponse(IncidentBase):
    id: int
    inmate_id: int
    reported_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AssignInmateRequest(BaseModel):
    inmate_id: int

class VisitationBookingRequest(BaseModel):
    inmate_id: int
    visitor_name: str
    date: date
    time_slot: str

# Endpoints

@router.get("/inmates", response_model=List[InmateResponse])
async def get_inmates(
    block: Optional[str] = None,
    security: Optional[SecurityLevel] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Inmate)
    if block:
        # Inmate doesn't have block directly, it's via Cell.
        query = query.join(Cell).where(Cell.block_id == block)
    if security:
        query = query.where(Inmate.security_level == security)

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/inmates/{id}/profile", response_model=InmateResponse)
async def get_inmate_profile(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Inmate).where(Inmate.id == id))
    inmate = result.scalar_one_or_none()
    if not inmate:
        raise HTTPException(status_code=404, detail="Inmate not found")
    return inmate

@router.get("/cells/occupancy", response_model=List[CellResponse])
async def get_cells_occupancy(block: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Cell)
    if block:
        query = query.where(Cell.block_id == block)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/cells/{id}/assign-inmate")
async def assign_inmate(id: int, request: AssignInmateRequest, db: AsyncSession = Depends(get_db)):
    # Check cell
    cell_result = await db.execute(select(Cell).where(Cell.id == id))
    cell = cell_result.scalar_one_or_none()
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")

    # Check inmate
    inmate_result = await db.execute(select(Inmate).where(Inmate.id == request.inmate_id))
    inmate = inmate_result.scalar_one_or_none()
    if not inmate:
        raise HTTPException(status_code=404, detail="Inmate not found")

    # If inmate is already in this cell, do nothing
    if inmate.cell_id == cell.id:
        return {"message": "Inmate already assigned to this cell"}

    if cell.current_occupancy >= cell.capacity:
        raise HTTPException(status_code=400, detail="Cell is full")

    # If inmate was in another cell, decrement its occupancy
    if inmate.cell_id is not None:
        old_cell_result = await db.execute(select(Cell).where(Cell.id == inmate.cell_id))
        old_cell = old_cell_result.scalar_one_or_none()
        if old_cell:
            old_cell.current_occupancy = max(0, old_cell.current_occupancy - 1)
            if old_cell.current_occupancy == 0:
                old_cell.status = CellStatus.VACANT

    inmate.cell_id = cell.id
    cell.current_occupancy += 1
    cell.status = CellStatus.OCCUPIED

    await db.commit()
    return {"message": "Inmate assigned to cell"}

@router.post("/incidents/report", response_model=IncidentResponse)
async def report_incident(incident: IncidentCreate, db: AsyncSession = Depends(get_db)):
    db_incident = Incident(**incident.model_dump())
    db.add(db_incident)
    await db.commit()
    await db.refresh(db_incident)
    return db_incident

@router.get("/incidents/active", response_model=List[IncidentResponse])
async def get_active_incidents(db: AsyncSession = Depends(get_db)):
    # Assume active means not RESOLVED
    query = select(Incident).where(Incident.status != IncidentStatus.RESOLVED)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/visitation/schedule")
async def get_visitation_schedule(inmate_id: int):
    # Mock response
    return {"inmate_id": inmate_id, "schedule": []}

@router.post("/visitation/book")
async def book_visitation(booking: VisitationBookingRequest):
    # Mock response
    return {"message": "Visitation booked", "details": booking}

@router.get("/analytics/population-trend")
async def get_population_trend(db: AsyncSession = Depends(get_db)):
    # Mock logic: return current population
    result = await db.execute(select(func.count(Inmate.id)))
    count = result.scalar()
    return {"current_population": count, "trend": "stable"}
