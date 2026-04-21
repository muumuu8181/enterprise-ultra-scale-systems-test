from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field, ConfigDict

from src.database import get_db
from src.models.gallery_models import (
    Artwork, Exhibition, Sale,
    ArtworkLocation, ExhibitionStatus, SaleType, PaymentStatus
)

router = APIRouter()

# --- Schemas ---

class ArtworkBase(BaseModel):
    title: str
    artist_id: int
    medium: Optional[str] = None
    dimensions: Optional[str] = None
    year_created: Optional[int] = None
    edition: Optional[str] = None
    price: Optional[float] = None
    reserve_price: Optional[float] = None
    location: Optional[ArtworkLocation] = ArtworkLocation.STORAGE
    condition: Optional[str] = None
    provenance: Optional[List[Dict[str, Any]]] = None

class ArtworkCreate(ArtworkBase):
    pass

class ArtworkResponse(ArtworkBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class ExhibitionBase(BaseModel):
    gallery_id: int
    title: str
    curator: Optional[str] = None
    theme: Optional[str] = None
    opening_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    artworks: Optional[List[int]] = None
    catalog_url: Optional[str] = None
    status: Optional[ExhibitionStatus] = ExhibitionStatus.PLANNING

class ExhibitionCreate(ExhibitionBase):
    pass

class ExhibitionResponse(ExhibitionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class SaleCreate(BaseModel):
    artwork_id: int
    buyer_id: int
    sale_type: SaleType
    hammer_price: float
    commission_pct: float
    payment_status: Optional[PaymentStatus] = PaymentStatus.PENDING

class SaleResponse(BaseModel):
    id: int
    artwork_id: int
    buyer_id: int
    sale_type: SaleType
    hammer_price: float
    commission_pct: float
    total_amount: float
    payment_status: PaymentStatus
    sold_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AppraisalResponse(BaseModel):
    artwork_id: int
    estimated_value: float
    confidence_score: float
    appraisal_date: datetime

class SalesTrendResponse(BaseModel):
    period: str
    total_sales: float
    transaction_count: int

# --- Endpoints ---

@router.get("/artworks", response_model=List[ArtworkResponse])
def get_artworks(
    artist: Optional[str] = None, # Using str as proxy for name filter or ID if int? Prompt says 'artist='
    medium: Optional[str] = None,
    available: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Artwork)
    if artist:
        # Assuming artist search by ID if it's an int, or ignoring if we don't have Artist model joined.
        # Since artist_id is int, let's assume 'artist' param is an ID for simplicity, or we can't really filter by name without an Artist model.
        # But commonly 'artist' query param might be name. I'll check if it's a number.
        if artist.isdigit():
             query = query.filter(Artwork.artist_id == int(artist))
        # If it's a name, we can't filter easily without a join. I'll stick to ID support or simple implementation.

    if medium:
        query = query.filter(Artwork.medium.ilike(f"%{medium}%"))

    if available is not None:
        if available:
            query = query.filter(Artwork.location != ArtworkLocation.SOLD)
        else:
            query = query.filter(Artwork.location == ArtworkLocation.SOLD)

    return query.all()

@router.get("/artworks/{id}/detail", response_model=ArtworkResponse)
def get_artwork_detail(id: int, db: Session = Depends(get_db)):
    artwork = db.query(Artwork).filter(Artwork.id == id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return artwork

@router.get("/exhibitions", response_model=List[ExhibitionResponse])
def get_exhibitions(status: Optional[ExhibitionStatus] = None, db: Session = Depends(get_db)):
    query = db.query(Exhibition)
    if status:
        query = query.filter(Exhibition.status == status)
    return query.all()

@router.post("/exhibitions/create", response_model=ExhibitionResponse, status_code=status.HTTP_201_CREATED)
def create_exhibition(exhibition: ExhibitionCreate, db: Session = Depends(get_db)):
    db_exhibition = Exhibition(**exhibition.model_dump())
    db.add(db_exhibition)
    db.commit()
    db.refresh(db_exhibition)
    return db_exhibition

@router.post("/sales/record", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def record_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    # Calculate total amount
    total_amount = sale.hammer_price * (1 + sale.commission_pct / 100)

    db_sale = Sale(
        **sale.model_dump(),
        total_amount=total_amount
    )

    # Update artwork status
    artwork = db.query(Artwork).filter(Artwork.id == sale.artwork_id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    if artwork.location == ArtworkLocation.SOLD:
        raise HTTPException(status_code=400, detail="Artwork already sold")

    artwork.location = ArtworkLocation.SOLD

    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale

@router.get("/sales/history", response_model=List[SaleResponse])
def get_sales_history(period: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Sale)
    if period:
        # Simple period filtering
        now = datetime.utcnow()
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = None

        if start_date:
            query = query.filter(Sale.sold_at >= start_date)

    return query.all()

@router.get("/artists/{id}/portfolio", response_model=List[ArtworkResponse])
def get_artist_portfolio(id: int, db: Session = Depends(get_db)):
    return db.query(Artwork).filter(Artwork.artist_id == id).all()

@router.get("/analytics/sales-trend", response_model=SalesTrendResponse)
def get_sales_trend(db: Session = Depends(get_db)):
    # Simple aggregation
    total_sales = db.query(func.sum(Sale.total_amount)).scalar() or 0.0
    count = db.query(Sale).count()
    return SalesTrendResponse(
        period="all_time",
        total_sales=total_sales,
        transaction_count=count
    )

@router.post("/artworks/{id}/appraise", response_model=AppraisalResponse)
def appraise_artwork(id: int, db: Session = Depends(get_db)):
    artwork = db.query(Artwork).filter(Artwork.id == id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    # Mock appraisal logic
    # Estimate value based on last price + random factor or just a placeholder
    estimated_value = (artwork.price or 0) * 1.1 if artwork.price else 1000.0

    return AppraisalResponse(
        artwork_id=id,
        estimated_value=estimated_value,
        confidence_score=0.85,
        appraisal_date=datetime.utcnow()
    )
