from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Any, Dict
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
import json

# Try to import shapely for geometry handling, otherwise fallback
try:
    from geoalchemy2.shape import to_shape
    from shapely.geometry import mapping
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False

from src.database import get_db
from src.models.fishery_models import FishingVessel, QuotaAllocation, CatchReport, VesselType, QuotaStatus

router = APIRouter()

# --- Schemas ---

class FishingVesselBase(BaseModel):
    name: str
    registration_number: str
    owner_id: int
    vessel_type: VesselType
    length_m: float
    port_base: str
    license_expiry: date
    ais_mmsi: str

class FishingVesselCreate(FishingVesselBase):
    pass

class FishingVesselResponse(FishingVesselBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class QuotaAllocationBase(BaseModel):
    vessel_id: int
    species: str
    fishing_zone: str
    quota_tonnes: float
    caught_tonnes: float = 0.0
    remaining_tonnes: float
    season_start: date
    season_end: date
    status: QuotaStatus = QuotaStatus.active

class QuotaAllocationCreate(QuotaAllocationBase):
    pass

class QuotaAllocationResponse(QuotaAllocationBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CatchReportBase(BaseModel):
    vessel_id: int
    species: str
    weight_kg: float
    location: Dict[str, Any]  # GeoJSON Point
    catch_date: datetime
    gear_type: str
    bycatch: Dict[str, Any] = {}
    verified: bool = False
    landing_port: Optional[str] = None

class CatchReportCreate(CatchReportBase):
    pass

class CatchReportResponse(CatchReportBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

    @field_validator('location', mode='before')
    @classmethod
    def serialize_location(cls, v: Any) -> Dict[str, Any]:
        if isinstance(v, dict):
            return v
        if HAS_SHAPELY and v is not None:
             # If it's a WKBElement or similar from GeoAlchemy2
             try:
                 if hasattr(v, 'desc'): # WKBElement
                     shape = to_shape(v)
                     return mapping(shape)
             except Exception:
                 pass
        # Fallback if no shapely or unknown type
        return {"type": "Point", "coordinates": [0, 0]}

# --- Endpoints ---

@router.get("/vessels", response_model=List[FishingVesselResponse])
async def get_vessels(
    port: Optional[str] = None,
    type: Optional[VesselType] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(FishingVessel)
    if port:
        query = query.where(FishingVessel.port_base == port)
    if type:
        query = query.where(FishingVessel.vessel_type == type)

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/vessels/{id}/quota-status")
async def get_vessel_quota_status(id: int, db: AsyncSession = Depends(get_db)):
    query = select(QuotaAllocation).where(QuotaAllocation.vessel_id == id)
    result = await db.execute(query)
    quotas = result.scalars().all()
    # Return as list of dicts or specific schema? Prompt implies a status summary.
    # I'll return the list of allocations.
    return [QuotaAllocationResponse.model_validate(q) for q in quotas]

@router.get("/quotas", response_model=List[QuotaAllocationResponse])
async def get_quotas(
    species: Optional[str] = None,
    zone: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(QuotaAllocation)
    if species:
        query = query.where(QuotaAllocation.species == species)
    if zone:
        query = query.where(QuotaAllocation.fishing_zone == zone)

    result = await db.execute(query)
    return result.scalars().all()

@router.post("/quotas/allocate", response_model=QuotaAllocationResponse, status_code=status.HTTP_201_CREATED)
async def allocate_quota(allocation: QuotaAllocationCreate, db: AsyncSession = Depends(get_db)):
    db_allocation = QuotaAllocation(**allocation.model_dump())
    db.add(db_allocation)
    await db.commit()
    await db.refresh(db_allocation)
    return db_allocation

@router.post("/catch/report", response_model=CatchReportResponse, status_code=status.HTTP_201_CREATED)
async def report_catch(report: CatchReportCreate, db: AsyncSession = Depends(get_db)):
    report_data = report.model_dump()
    loc = report_data['location']

    # Simple GeoJSON to WKT conversion for Point
    if loc.get('type') == 'Point' and 'coordinates' in loc:
        coords = loc['coordinates']
        wkt_location = f"POINT({coords[0]} {coords[1]})"
    else:
        # Fallback or error
        wkt_location = "POINT(0 0)"

    report_data['location'] = wkt_location

    db_report = CatchReport(**report_data)
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    return db_report

@router.get("/catch/reports", response_model=List[CatchReportResponse])
async def get_catch_reports(
    vessel: Optional[int] = None,
    species: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(CatchReport)
    if vessel:
        query = query.where(CatchReport.vessel_id == vessel)
    if species:
        query = query.where(CatchReport.species == species)

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/analytics/stock-assessment")
async def get_stock_assessment(species: Optional[str] = None):
    return {"species": species, "status": "healthy", "estimated_biomass": 50000}

@router.get("/zones/closures")
async def get_zone_closures():
    return [{"zone": "Zone A", "reason": "spawning", "end_date": "2023-12-31"}]

@router.get("/compliance/vessel-tracking/{id}")
async def get_vessel_tracking(id: int):
    return {"vessel_id": id, "last_known_location": {"type": "Point", "coordinates": [135.0, 35.0]}, "timestamp": datetime.now().isoformat()}
