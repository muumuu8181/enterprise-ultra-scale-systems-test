from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict, field_validator
from geoalchemy2.shape import to_shape
import shapely.geometry
from shapely.geometry import shape

from src.database import get_db
from src.models.disaster_models import (
    DisasterEvent, ReliefOperation, AidShipment,
    DisasterType, SeverityLevel, DisasterStatus,
    OperationType, OperationStatus, ShipmentStatus
)

router = APIRouter()

# --- Schemas ---

class DisasterEventCreate(BaseModel):
    event_type: DisasterType
    severity: SeverityLevel
    location: Dict[str, Any]  # GeoJSON Geometry
    affected_area_sq_km: Optional[float] = None
    affected_population: Optional[int] = None
    start_date: datetime

class DisasterEventResponse(DisasterEventCreate):
    id: int
    status: DisasterStatus
    model_config = ConfigDict(from_attributes=True)

    @field_validator("location", mode="before")
    @classmethod
    def wkb_to_geojson(cls, v):
        # If it's a WKBElement (from DB), convert to GeoJSON dict
        if hasattr(v, "desc") or hasattr(v, "data"):
             s = to_shape(v)
             return shapely.geometry.mapping(s)
        return v

class ReliefOperationCreate(BaseModel):
    event_id: int
    operation_type: OperationType
    lead_agency: str
    personnel_deployed: int = 0
    resources: Dict[str, Any] = {}

class ReliefOperationResponse(ReliefOperationCreate):
    id: int
    status: OperationStatus
    model_config = ConfigDict(from_attributes=True)

class AidShipmentCreate(BaseModel):
    operation_id: int
    contents: Dict[str, Any]
    weight_kg: float
    origin: str
    destination: str
    carrier: str
    eta: Optional[datetime] = None
    tracking_number: str

class AidShipmentResponse(AidShipmentCreate):
    id: int
    status: ShipmentStatus
    model_config = ConfigDict(from_attributes=True)

class NeedsAssessmentResponse(BaseModel):
    event_id: int
    immediate_needs: List[str]
    priority_level: str
    estimated_funding_required: float

class AnalyticsResponse(BaseModel):
    response_effectiveness_score: float
    average_deployment_time_hours: float
    resources_utilized_pct: float

class ShelterCapacityResponse(BaseModel):
    location: str
    total_capacity: int
    current_occupancy: int
    available_slots: int

# --- Endpoints ---

@router.get("/events/active", response_model=List[DisasterEventResponse])
async def get_active_events(db: AsyncSession = Depends(get_db)):
    stmt = select(DisasterEvent).where(DisasterEvent.status == DisasterStatus.ACTIVE)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/events/declare", response_model=DisasterEventResponse)
async def declare_event(event: DisasterEventCreate, db: AsyncSession = Depends(get_db)):
    try:
        geom_wkt = shape(event.location).wkt
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid GeoJSON: {str(e)}")

    db_event = DisasterEvent(
        event_type=event.event_type,
        severity=event.severity,
        location=geom_wkt,
        affected_area_sq_km=event.affected_area_sq_km,
        affected_population=event.affected_population,
        start_date=event.start_date,
        status=DisasterStatus.ACTIVE
    )
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event

@router.get("/operations/{event_id}/overview", response_model=List[ReliefOperationResponse])
async def get_operations_overview(event_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(ReliefOperation).where(ReliefOperation.event_id == event_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/operations/deploy", response_model=ReliefOperationResponse)
async def deploy_operation(op: ReliefOperationCreate, db: AsyncSession = Depends(get_db)):
    db_op = ReliefOperation(
        event_id=op.event_id,
        operation_type=op.operation_type,
        lead_agency=op.lead_agency,
        personnel_deployed=op.personnel_deployed,
        resources=op.resources,
        status=OperationStatus.MOBILIZING
    )
    db.add(db_op)
    await db.commit()
    await db.refresh(db_op)
    return db_op

@router.post("/shipments/dispatch", response_model=AidShipmentResponse)
async def dispatch_shipment(shipment: AidShipmentCreate, db: AsyncSession = Depends(get_db)):
    db_shipment = AidShipment(
        operation_id=shipment.operation_id,
        contents=shipment.contents,
        weight_kg=shipment.weight_kg,
        origin=shipment.origin,
        destination=shipment.destination,
        carrier=shipment.carrier,
        status=ShipmentStatus.PREPARING,
        eta=shipment.eta,
        tracking_number=shipment.tracking_number
    )
    db.add(db_shipment)
    await db.commit()
    await db.refresh(db_shipment)
    return db_shipment

@router.get("/shipments/{id}/track", response_model=AidShipmentResponse)
async def track_shipment(id: int, db: AsyncSession = Depends(get_db)):
    shipment = await db.get(AidShipment, id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment

@router.get("/needs-assessment/{event_id}", response_model=NeedsAssessmentResponse)
async def get_needs_assessment(event_id: int, db: AsyncSession = Depends(get_db)):
    # Mock implementation
    return NeedsAssessmentResponse(
        event_id=event_id,
        immediate_needs=["clean_water", "tents", "medical_supplies"],
        priority_level="high",
        estimated_funding_required=5000000.0
    )

@router.get("/analytics/response-effectiveness", response_model=AnalyticsResponse)
async def get_analytics():
    # Mock implementation
    return AnalyticsResponse(
        response_effectiveness_score=0.85,
        average_deployment_time_hours=12.5,
        resources_utilized_pct=92.0
    )

@router.get("/shelters/capacity", response_model=ShelterCapacityResponse)
async def get_shelter_capacity(location: str = Query(..., description="Location to check")):
    # Mock implementation
    return ShelterCapacityResponse(
        location=location,
        total_capacity=1000,
        current_occupancy=750,
        available_slots=250
    )
