from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from geoalchemy2.elements import WKTElement
from src.database import get_db
from src.models.city_models import EmergencyIncident
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime

router = APIRouter(prefix="/emergency", tags=["emergency"])

# Schemas
class IncidentResponse(BaseModel):
    id: int
    incident_type: str
    status: str
    priority: int
    units_dispatched: List[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IncidentCreate(BaseModel):
    incident_type: str
    latitude: float
    longitude: float
    priority: int
    status: str = "REPORTED"

class DispatchRequest(BaseModel):
    unit_ids: List[str]

@router.post("/incidents", response_model=IncidentResponse)
async def create_incident(incident: IncidentCreate, db: AsyncSession = Depends(get_db)):
    """
    インシデント作成
    """
    point = f"POINT({incident.longitude} {incident.latitude})"
    new_incident = EmergencyIncident(
        incident_type=incident.incident_type,
        location=WKTElement(point, srid=4326),
        status=incident.status,
        priority=incident.priority,
        created_at=datetime.utcnow(),
        units_dispatched=[]
    )
    db.add(new_incident)
    await db.commit()
    await db.refresh(new_incident)
    return new_incident

@router.get("/incidents/active", response_model=List[IncidentResponse])
async def get_active_incidents(db: AsyncSession = Depends(get_db)):
    """
    アクティブ一覧 (priority順)
    """
    stmt = select(EmergencyIncident).where(EmergencyIncident.status != "CLEARED").order_by(EmergencyIncident.priority.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/incidents/{id}", response_model=IncidentResponse)
async def get_incident(id: int, db: AsyncSession = Depends(get_db)):
    """
    詳細取得
    """
    stmt = select(EmergencyIncident).where(EmergencyIncident.id == id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.put("/incidents/{id}/dispatch")
async def dispatch_units(id: int, request: DispatchRequest, db: AsyncSession = Depends(get_db)):
    """
    出動指令 (unit_ids list)
    """
    stmt = update(EmergencyIncident).where(EmergencyIncident.id == id).values(
        units_dispatched=request.unit_ids,
        status="DISPATCHED"
    )
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
         raise HTTPException(status_code=404, detail="Incident not found")

    return {"message": "Units dispatched", "unit_ids": request.unit_ids}
