from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from datetime import date, datetime
from pydantic import BaseModel, field_validator

from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKBElement
from shapely.geometry import mapping

from src.database import get_db
from src.models.vineyard_models import Vineyard, HarvestBatch, WineLot, QualityGrade, WineType, WineStatus

router = APIRouter()

# --- Pydantic Schemas ---

class VineyardBase(BaseModel):
    name: str
    location: Any  # GeoJSON
    area_hectares: float
    grape_varieties: List[str]
    soil_type: Optional[str] = None
    elevation_m: Optional[float] = None
    climate_zone: Optional[str] = None
    organic_certified: bool = False

class VineyardCreate(VineyardBase):
    pass

class VineyardResponse(VineyardBase):
    id: int

    @field_validator('location', mode='before')
    @classmethod
    def serialize_location(cls, v):
        if isinstance(v, WKBElement) or hasattr(v, "desc"):
            return mapping(to_shape(v))
        return v

    class Config:
        from_attributes = True

class HarvestLog(BaseModel):
    vineyard_id: int
    variety: str
    harvest_date: date
    weight_kg: float
    brix_level: float
    ph: float
    acidity: float
    quality_grade: QualityGrade
    destination_tank_id: Optional[str] = None

class HarvestBatchResponse(HarvestLog):
    id: int
    class Config:
        from_attributes = True

class WineLotBase(BaseModel):
    batch_ids: List[int]
    wine_type: WineType
    fermentation_start: Optional[datetime] = None
    fermentation_end: Optional[datetime] = None
    aging_vessel: Optional[str] = None # Using str for Enum in schema for simplicity
    volume_liters: float
    status: WineStatus

class WineLotResponse(WineLotBase):
    id: int
    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/vineyards", response_model=List[VineyardResponse])
def get_vineyards(
    variety: Optional[str] = None,
    organic: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Vineyard)
    if organic is not None:
        query = query.filter(Vineyard.organic_certified == organic)

    if variety:
        all_vineyards = query.all()
        return [v for v in all_vineyards if variety in v.grape_varieties]

    return query.all()

@router.get("/vineyards/{id}/soil-analysis")
def get_soil_analysis(id: int, db: Session = Depends(get_db)):
    vineyard = db.query(Vineyard).filter(Vineyard.id == id).first()
    if not vineyard:
        raise HTTPException(status_code=404, detail="Vineyard not found")

    return {
        "vineyard_id": id,
        "soil_type": vineyard.soil_type,
        "ph_level": 6.5, # Mock
        "organic_matter_percent": 2.5, # Mock
        "last_analyzed": "2023-10-01"
    }

@router.post("/harvest/log", response_model=HarvestBatchResponse)
def log_harvest(harvest_data: HarvestLog, db: Session = Depends(get_db)):
    db_harvest = HarvestBatch(**harvest_data.dict())
    db.add(db_harvest)
    db.commit()
    db.refresh(db_harvest)
    return db_harvest

@router.get("/harvest/{vineyard_id}/season-summary")
def get_season_summary(vineyard_id: int, db: Session = Depends(get_db)):
    batches = db.query(HarvestBatch).filter(HarvestBatch.vineyard_id == vineyard_id).all()
    if not batches:
         return {"vineyard_id": vineyard_id, "message": "No harvest data found"}

    total_weight = sum(b.weight_kg for b in batches)
    avg_brix = sum(b.brix_level for b in batches) / len(batches) if batches else 0

    return {
        "vineyard_id": vineyard_id,
        "total_harvest_weight_kg": total_weight,
        "average_brix": avg_brix,
        "batch_count": len(batches)
    }

@router.get("/lots", response_model=List[WineLotResponse])
def get_lots(
    type: Optional[WineType] = None,
    status: Optional[WineStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(WineLot)
    if type:
        query = query.filter(WineLot.wine_type == type)
    if status:
        query = query.filter(WineLot.status == status)
    return query.all()

@router.get("/lots/{id}/tasting-notes")
def get_tasting_notes(id: int, db: Session = Depends(get_db)):
    lot = db.query(WineLot).filter(WineLot.id == id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Wine lot not found")

    # Mock notes
    return {
        "lot_id": id,
        "notes": [
            {"date": "2023-11-01", "taster": "Sommelier A", "score": 92, "comments": "Fruity with hints of oak."},
            {"date": "2023-12-15", "taster": "Sommelier B", "score": 94, "comments": "Developing well, good structure."}
        ]
    }

@router.get("/analytics/yield-trend")
def get_yield_trend(db: Session = Depends(get_db)):
    # Mock trend data
    return {
        "years": [2020, 2021, 2022, 2023],
        "average_yield_per_hectare": [5000, 4800, 5200, 5100] # kg/ha
    }

@router.get("/weather/{vineyard_id}/forecast")
def get_weather_forecast(vineyard_id: int, db: Session = Depends(get_db)):
    vineyard = db.query(Vineyard).filter(Vineyard.id == vineyard_id).first()
    if not vineyard:
        raise HTTPException(status_code=404, detail="Vineyard not found")

    loc = vineyard.location
    if isinstance(loc, WKBElement) or hasattr(loc, "desc"):
        loc = mapping(to_shape(loc))

    # Mock forecast
    return {
        "vineyard_id": vineyard_id,
        "location": loc,
        "forecast": [
            {"day": "Monday", "temp_high": 25, "temp_low": 15, "condition": "Sunny"},
            {"day": "Tuesday", "temp_high": 24, "temp_low": 14, "condition": "Cloudy"},
        ]
    }
