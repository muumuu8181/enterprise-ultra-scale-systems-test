from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.services.valuation_service import estimate_value, ValuationResult

router = APIRouter()

# Schemas
class PropertyCreate(BaseModel):
    address: str
    property_type: str
    bedrooms: int
    area_sqm: float
    year_built: int
    list_price: float

class PropertyResponse(PropertyCreate):
    id: int
    status: str

class OfferCreate(BaseModel):
    property_id: int
    buyer_id: str
    offer_price: float
    contingencies: Dict[str, Any]
    expiry_date: datetime

class OfferResponse(OfferCreate):
    id: int
    status: str

@router.post("/properties/list", response_model=PropertyResponse)
async def list_property(prop: PropertyCreate):
    return PropertyResponse(
        id=1,
        status="listed",
        **prop.model_dump()
    )

@router.get("/properties/search", response_model=List[PropertyResponse])
async def search_properties(
    city: Optional[str] = Query(None),
    property_type: Optional[str] = Query(None, alias="type"),
    price_max: Optional[float] = Query(None)
):
    # Dummy result
    return [
        PropertyResponse(
            id=1,
            address="123 Main St",
            property_type="residential",
            bedrooms=3,
            area_sqm=120.0,
            year_built=2010,
            list_price=500000.0,
            status="listed"
        )
    ]

@router.get("/properties/{id}/valuation", response_model=ValuationResult)
async def get_valuation(id: int):
    return await estimate_value(id)

@router.get("/properties/{id}/history")
async def get_history(id: int):
    return [
        {"date": "2020-01-01", "event": "listed", "price": 400000},
        {"date": "2020-02-01", "event": "sold", "price": 395000}
    ]

@router.post("/offers/submit", response_model=OfferResponse)
async def submit_offer(offer: OfferCreate):
    return OfferResponse(
        id=101,
        status="pending",
        **offer.model_dump()
    )

@router.get("/offers/{property_id}/all", response_model=List[OfferResponse])
async def get_offers(property_id: int):
    return [
        OfferResponse(
            id=101,
            property_id=property_id,
            buyer_id="buyer_001",
            offer_price=490000.0,
            contingencies={"inspection": True},
            expiry_date=datetime.now(),
            status="pending"
        )
    ]
