from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from src.database import get_db
from src.models.waste_models import WasteContainer, StorageFacility, TransportManifest, ContainerType, WasteClass, FacilityType, TransportStatus

router = APIRouter()

# Schemas
class WasteContainerBase(BaseModel):
    container_type: ContainerType
    waste_class: WasteClass
    isotopes: Dict
    activity_becquerels: float
    weight_kg: float
    storage_location_id: Optional[int] = None
    integrity_status: str
    last_inspected: datetime

class WasteContainerCreate(WasteContainerBase):
    pass

class WasteContainerResponse(WasteContainerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class StorageFacilityBase(BaseModel):
    name: str
    facility_type: FacilityType
    location: str
    capacity_containers: int
    current_occupancy: int = 0
    license_expiry: datetime
    operator_id: str

class StorageFacilityCreate(StorageFacilityBase):
    pass

class StorageFacilityResponse(StorageFacilityBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class TransportManifestBase(BaseModel):
    container_ids: List[int]
    origin_id: int
    destination_id: int
    carrier: str
    vehicle_id: str
    route: str
    departure_time: datetime
    arrival_time: Optional[datetime] = None
    status: TransportStatus = TransportStatus.planned
    regulatory_approval: bool = False

class TransportManifestCreate(TransportManifestBase):
    pass

class TransportManifestResponse(TransportManifestBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class InspectionScheduleRequest(BaseModel):
    container_id: int
    date: datetime
    inspector_id: str

# Endpoints

@router.get("/containers", response_model=List[WasteContainerResponse])
async def get_containers(
    waste_class: Optional[WasteClass] = Query(None, alias="class"),
    facility_id: Optional[int] = Query(None, alias="facility"),
    db: AsyncSession = Depends(get_db)
):
    query = select(WasteContainer)
    if waste_class:
        query = query.where(WasteContainer.waste_class == waste_class)
    if facility_id:
        query = query.where(WasteContainer.storage_location_id == facility_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/containers/{id}/radiation-log")
async def get_radiation_log(id: int):
    # Mock response
    return {"container_id": id, "logs": [{"timestamp": datetime.now(), "level_sv": 0.05}]}

@router.get("/facilities", response_model=List[StorageFacilityResponse])
async def get_facilities(
    facility_type: Optional[FacilityType] = Query(None, alias="type"),
    db: AsyncSession = Depends(get_db)
):
    query = select(StorageFacility)
    if facility_type:
        query = query.where(StorageFacility.facility_type == facility_type)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/facilities/{id}/capacity")
async def get_facility_capacity(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StorageFacility).where(StorageFacility.id == id))
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return {
        "id": facility.id,
        "capacity_containers": facility.capacity_containers,
        "current_occupancy": facility.current_occupancy,
        "available": facility.capacity_containers - facility.current_occupancy
    }

@router.post("/transport/plan", response_model=TransportManifestResponse)
async def plan_transport(manifest: TransportManifestCreate, db: AsyncSession = Depends(get_db)):
    db_manifest = TransportManifest(**manifest.model_dump())
    db.add(db_manifest)
    await db.commit()
    await db.refresh(db_manifest)
    return db_manifest

@router.get("/transport/{id}/track")
async def track_transport(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TransportManifest).where(TransportManifest.id == id))
    manifest = result.scalar_one_or_none()
    if not manifest:
        raise HTTPException(status_code=404, detail="Transport not found")
    return {"id": id, "status": manifest.status, "current_location": "En route (mock)"}

@router.get("/compliance/inventory-report")
async def inventory_report():
    return {"total_waste_kg": 1000.0, "compliance_status": "compliant", "generated_at": datetime.now()}

@router.get("/compliance/dose-records")
async def dose_records():
    return [{"worker_id": "W123", "dose_msv": 1.2, "date": datetime.now()}]

@router.post("/inspections/schedule")
async def schedule_inspection(request: InspectionScheduleRequest):
    return {"status": "scheduled", "container_id": request.container_id, "date": request.date, "inspector_id": request.inspector_id}
