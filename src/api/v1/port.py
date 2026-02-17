from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from src.database import get_db
from src.services.port_service import berth_planning, check_sanctions, calculate_port_dues, BerthAssignment, SanctionsResult
from src.models.cargo_models import CargoType, DeclarationType

router = APIRouter()

# Schemas
class VesselScheduleItem(BaseModel):
    vessel_id: str
    eta: datetime
    etd: Optional[datetime] = None

class BerthAvailability(BaseModel):
    berth_id: str
    is_available: bool
    next_available: Optional[datetime]

class PortCallCreate(BaseModel):
    vessel_id: str
    port_id: str
    eta: datetime

class PortCallResponse(BaseModel):
    id: int
    vessel_id: str
    port_id: str
    berth_id: str
    status: str

class CargoManifest(BaseModel):
    items: List[Dict[str, Any]]

class CustomsDeclarationCreate(BaseModel):
    vessel_id: str
    port_id: str
    declaration_type: DeclarationType
    cargo_manifest: Dict[str, Any]

class CustomsStatus(BaseModel):
    id: int
    status: str
    inspection_required: bool

# Endpoints

@router.get("/ports/{id}/vessel-schedule", response_model=List[VesselScheduleItem])
async def get_vessel_schedule(id: str, db: AsyncSession = Depends(get_db)):
    """Get the vessel schedule for a port."""
    # Placeholder implementation
    return []

@router.get("/ports/{id}/berth-availability", response_model=List[BerthAvailability])
async def get_berth_availability(id: str, db: AsyncSession = Depends(get_db)):
    """Check berth availability at a port."""
    # Placeholder implementation
    return [
        BerthAvailability(berth_id="B-01", is_available=True, next_available=None)
    ]

@router.post("/port-calls/register", response_model=PortCallResponse)
async def register_port_call(data: PortCallCreate, db: AsyncSession = Depends(get_db)):
    """Register a new port call."""
    # 1. Check sanctions
    sanctions = await check_sanctions(data.vessel_id)
    if sanctions.is_sanctioned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Vessel is sanctioned: {sanctions.reason}"
        )

    # 2. Plan berth
    berth_assignment = await berth_planning(data.port_id, data.vessel_id, data.eta)

    # 3. Create PortCall (mock)
    # In a real app, we would save to DB here.
    return PortCallResponse(
        id=1,
        vessel_id=data.vessel_id,
        port_id=data.port_id,
        berth_id=berth_assignment.berth_id,
        status="registered"
    )

@router.get("/port-calls/{id}/cargo", response_model=CargoManifest)
async def get_port_call_cargo(id: int, db: AsyncSession = Depends(get_db)):
    """Get cargo manifest for a port call."""
    # Placeholder implementation
    return CargoManifest(items=[])

@router.post("/customs/declarations", response_model=CustomsStatus)
async def create_customs_declaration(data: CustomsDeclarationCreate, db: AsyncSession = Depends(get_db)):
    """Submit a customs declaration."""
    # Placeholder implementation
    return CustomsStatus(id=1, status="submitted", inspection_required=False)

@router.get("/customs/{id}/status", response_model=CustomsStatus)
async def get_customs_status(id: int, db: AsyncSession = Depends(get_db)):
    """Check status of a customs declaration."""
    # Placeholder implementation
    return CustomsStatus(id=id, status="cleared", inspection_required=False)
