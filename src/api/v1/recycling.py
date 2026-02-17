from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.recycling_models import CollectionPoint, RecyclingBatch, MarketPrice, PointType, MaterialType, BatchStatus, PriceTrend
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

router = APIRouter()

# --- Response Models ---
class CollectionPointResponse(BaseModel):
    id: int
    name: str
    location: Dict[str, Any]
    fill_level_pct: float
    point_type: PointType
    next_pickup: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

    @field_validator('location', mode='before')
    @classmethod
    def parse_location(cls, v):
        try:
            return mapping(to_shape(v))
        except Exception:
            return v

class BatchResponse(BaseModel):
    id: int
    material: MaterialType
    weight_kg: float
    status: BatchStatus

    model_config = ConfigDict(from_attributes=True)

class MarketPriceResponse(BaseModel):
    material: MaterialType
    price_per_kg: float
    trend: PriceTrend
    effective_date: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Request Models ---
class BatchCreate(BaseModel):
    collection_point_id: int
    material: MaterialType
    weight_kg: float
    contamination_pct: float
    destination_facility_id: int

# --- API Endpoints ---

@router.get("/collection-points", response_model=List[CollectionPointResponse])
def get_collection_points(
    type: Optional[PointType] = None,
    material: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CollectionPoint)
    if type:
        query = query.filter(CollectionPoint.point_type == type)

    results = query.all()

    if material:
        # Filter in Python assuming materials_accepted is a list of strings
        results = [p for p in results if p.materials_accepted and material in p.materials_accepted]

    return results

@router.get("/collection-points/{id}/fill-status")
def get_fill_status(id: int, db: Session = Depends(get_db)):
    point = db.query(CollectionPoint).filter(CollectionPoint.id == id).first()
    if not point:
        raise HTTPException(status_code=404, detail="Collection point not found")
    return {"id": point.id, "fill_level_pct": point.fill_level_pct}

@router.post("/batches/log", response_model=BatchResponse)
def log_batch(batch: BatchCreate, db: Session = Depends(get_db)):
    db_batch = RecyclingBatch(**batch.model_dump())
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

@router.get("/batches", response_model=List[BatchResponse])
def get_batches(
    material: Optional[MaterialType] = None,
    status: Optional[BatchStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(RecyclingBatch)
    if material:
        query = query.filter(RecyclingBatch.material == material)
    if status:
        query = query.filter(RecyclingBatch.status == status)
    return query.all()

@router.get("/market-prices", response_model=List[MarketPriceResponse])
def get_market_prices(
    material: Optional[MaterialType] = None,
    db: Session = Depends(get_db)
):
    query = db.query(MarketPrice)
    if material:
        query = query.filter(MarketPrice.material == material)
    return query.all()

@router.get("/analytics/diversion-rate")
def get_diversion_rate(db: Session = Depends(get_db)):
    # Mock calculation
    return {"diversion_rate": 0.45, "unit": "percentage"}

@router.post("/routes/optimize")
def optimize_routes():
    # Mock optimization triggers Celery task or similar
    return {"status": "optimization_started", "task_id": "mock-task-id-123"}

@router.get("/reports/environmental-impact")
def get_environmental_impact(period: str = "month"):
    # Mock report
    return {
        "period": period,
        "co2_saved_kg": 1500.5,
        "landfill_saved_kg": 5000.0,
        "energy_saved_kwh": 3200.0
    }
