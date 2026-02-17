from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.elements import WKTElement
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from src.database import get_db
from src.models.emergency_models import Incident, IncidentType, IncidentStatus, EmergencyUnit, Dispatch
from src.services.dispatch_service import DispatchService
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/incidents", tags=["Incidents"])

class IncidentCreate(BaseModel):
    incident_type: IncidentType
    latitude: float
    longitude: float
    severity: int = Field(..., ge=1, le=5)
    caller_info: Dict[str, Any]

class IncidentResponse(BaseModel):
    id: int
    incident_type: IncidentType
    severity: int
    status: IncidentStatus
    created_at: datetime
    caller_info: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class UnitResponse(BaseModel):
    id: int
    call_sign: str
    status: str
    model_config = ConfigDict(from_attributes=True)

@router.post("/create", response_model=IncidentResponse)
async def create_incident(
    incident_in: IncidentCreate,
    db: AsyncSession = Depends(get_db)
):
    point = f"POINT({incident_in.longitude} {incident_in.latitude})"
    new_incident = Incident(
        incident_type=incident_in.incident_type,
        location=WKTElement(point, srid=4326),
        severity=incident_in.severity,
        status=IncidentStatus.NEW,
        caller_info=incident_in.caller_info,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(new_incident)
    await db.commit()
    await db.refresh(new_incident)

    # Auto dispatch
    service = DispatchService(db)
    await service.auto_dispatch(new_incident)

    return new_incident

@router.get("/{id}/status", response_model=Dict[str, str])
async def get_incident_status(id: int, db: AsyncSession = Depends(get_db)):
    incident = await db.get(Incident, id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"status": incident.status.value}

@router.get("/active", response_model=List[IncidentResponse])
async def get_active_incidents(db: AsyncSession = Depends(get_db)):
    stmt = select(Incident).where(Incident.status != IncidentStatus.RESOLVED)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{id}/units", response_model=List[UnitResponse])
async def get_incident_units(id: int, db: AsyncSession = Depends(get_db)):
    incident = await db.get(Incident, id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    stmt = select(Dispatch).where(Dispatch.incident_id == id)
    result = await db.execute(stmt)
    dispatches = result.scalars().all()

    unit_ids = [d.unit_id for d in dispatches]
    if not unit_ids:
        return []

    stmt_units = select(EmergencyUnit).where(EmergencyUnit.id.in_(unit_ids))
    result_units = await db.execute(stmt_units)
    return result_units.scalars().all()

@router.post("/{id}/update")
async def update_incident(
    id: int,
    severity: Optional[int] = Body(None),
    status: Optional[IncidentStatus] = Body(None),
    db: AsyncSession = Depends(get_db)
):
    incident = await db.get(Incident, id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if severity is not None:
        incident.severity = severity
    if status is not None:
        incident.status = status

    await db.commit()
    await db.refresh(incident)
    return {"message": "Incident updated", "id": id}

@router.post("/{id}/close")
async def close_incident(id: int, db: AsyncSession = Depends(get_db)):
    incident = await db.get(Incident, id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = IncidentStatus.RESOLVED

    await db.commit()
    return {"message": "Incident closed", "id": id}
