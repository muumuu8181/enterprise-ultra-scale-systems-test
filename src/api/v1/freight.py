from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from src.database import get_db
from src.models.freight_models import (
    Shipment, Container, CustomsDeclaration,
    Mode, ShipmentStatus, ContainerType, ContainerStatus, CustomsStatus
)

router = APIRouter()

# --- Pydantic Schemas ---

class ContainerBase(BaseModel):
    container_type: ContainerType
    seal_number: str
    temperature_set_c: Optional[float] = None
    weight_kg: float
    status: ContainerStatus = ContainerStatus.EMPTY

class ContainerCreate(ContainerBase):
    pass

class ContainerResponse(ContainerBase):
    id: int
    shipment_id: int

    class Config:
        from_attributes = True

class CustomsDeclarationBase(BaseModel):
    hs_codes: Dict[str, Any] # JSON
    declared_value: float
    currency: str
    duties_amount: float
    broker_id: str
    status: CustomsStatus = CustomsStatus.DRAFT

class CustomsDeclarationCreate(CustomsDeclarationBase):
    shipment_id: int

class CustomsDeclarationResponse(CustomsDeclarationBase):
    id: int
    shipment_id: int

    class Config:
        from_attributes = True

class ShipmentBase(BaseModel):
    shipper_id: str
    consignee_id: str
    origin_port: str
    destination_port: str
    mode: Mode
    incoterm: str
    weight_kg: float
    volume_cbm: float
    status: ShipmentStatus = ShipmentStatus.BOOKED
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None

class ShipmentCreate(ShipmentBase):
    containers: List[ContainerCreate] = []

class ShipmentResponse(ShipmentBase):
    id: int
    containers: List[ContainerResponse] = []
    customs_declaration: Optional[CustomsDeclarationResponse] = None

    class Config:
        from_attributes = True

class TrackingEvent(BaseModel):
    timestamp: datetime
    location: str
    status: str
    description: str

class RateQuote(BaseModel):
    origin: str
    destination: str
    mode: Mode
    price: float
    currency: str
    valid_until: datetime

class BookingDocument(BaseModel):
    id: str
    type: str
    url: str

class TransitTimeAnalytics(BaseModel):
    lane: str
    average_transit_days: float
    p95_transit_days: float

# --- Endpoints ---

@router.get("/shipments", response_model=List[ShipmentResponse])
def get_shipments(
    mode: Optional[Mode] = None,
    status: Optional[ShipmentStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Shipment).options(
        joinedload(Shipment.containers),
        joinedload(Shipment.customs_declaration)
    )
    if mode:
        query = query.filter(Shipment.mode == mode)
    if status:
        query = query.filter(Shipment.status == status)
    return query.all()

@router.get("/shipments/{id}/track", response_model=List[TrackingEvent])
def track_shipment(id: int, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Mock tracking data
    return [
        TrackingEvent(
            timestamp=datetime.now(),
            location=shipment.origin_port,
            status="PICKED_UP",
            description="Cargo picked up from shipper"
        )
    ]

@router.post("/bookings/create", response_model=ShipmentResponse)
def create_booking(shipment: ShipmentCreate, db: Session = Depends(get_db)):
    db_shipment = Shipment(
        shipper_id=shipment.shipper_id,
        consignee_id=shipment.consignee_id,
        origin_port=shipment.origin_port,
        destination_port=shipment.destination_port,
        mode=shipment.mode,
        incoterm=shipment.incoterm,
        weight_kg=shipment.weight_kg,
        volume_cbm=shipment.volume_cbm,
        status=shipment.status,
        etd=shipment.etd,
        eta=shipment.eta
    )
    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)

    for container_data in shipment.containers:
        db_container = Container(
            shipment_id=db_shipment.id,
            **container_data.model_dump()
        )
        db.add(db_container)

    db.commit()
    db.refresh(db_shipment)
    return db_shipment

@router.get("/bookings/{id}/documents", response_model=List[BookingDocument])
def get_booking_documents(id: int, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Mock documents
    return [
        BookingDocument(id="doc_1", type="Bill of Lading", url=f"http://s3/docs/{id}/bol.pdf"),
        BookingDocument(id="doc_2", type="Commercial Invoice", url=f"http://s3/docs/{id}/invoice.pdf")
    ]

@router.get("/containers/{id}/location", response_model=TrackingEvent)
def get_container_location(id: int, db: Session = Depends(get_db)):
    container = db.query(Container).filter(Container.id == id).first()
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    # Mock location
    return TrackingEvent(
        timestamp=datetime.now(),
        location="35.6895° N, 139.6917° E", # Tokyo coordinates
        status=container.status,
        description="Current location from GPS seal"
    )

@router.get("/rates/quote", response_model=RateQuote)
def get_rate_quote(
    origin: str = Query(..., min_length=3),
    dest: str = Query(..., min_length=3),
    mode: Mode = Query(...)
):
    # Mock rate calculation logic
    base_price = 1000.0
    if mode == Mode.AIR:
        base_price *= 5
    elif mode == Mode.RAIL:
        base_price *= 0.8

    return RateQuote(
        origin=origin,
        destination=dest,
        mode=mode,
        price=base_price,
        currency="USD",
        valid_until=datetime.now()
    )

@router.post("/customs/declare", response_model=CustomsDeclarationResponse)
def declare_customs(declaration: CustomsDeclarationCreate, db: Session = Depends(get_db)):
    # Check if shipment exists
    shipment = db.query(Shipment).filter(Shipment.id == declaration.shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Check if declaration already exists
    if shipment.customs_declaration:
         raise HTTPException(status_code=400, detail="Customs declaration already exists for this shipment")

    db_declaration = CustomsDeclaration(
        **declaration.model_dump()
    )
    db.add(db_declaration)
    db.commit()
    db.refresh(db_declaration)

    return db_declaration

@router.get("/customs/{id}/status", response_model=Dict[str, str])
def get_customs_status(id: int, db: Session = Depends(get_db)):
    declaration = db.query(CustomsDeclaration).filter(CustomsDeclaration.id == id).first()
    if not declaration:
        raise HTTPException(status_code=404, detail="Customs declaration not found")

    return {"status": declaration.status, "last_updated": str(datetime.now())}

@router.get("/analytics/transit-times", response_model=TransitTimeAnalytics)
def get_transit_times(lane: str = Query(..., description="Format: ORIGIN-DEST")):
    # Mock analytics
    return TransitTimeAnalytics(
        lane=lane,
        average_transit_days=14.5,
        p95_transit_days=18.0
    )
