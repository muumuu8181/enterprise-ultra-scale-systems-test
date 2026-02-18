from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from geoalchemy2 import WKBElement
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
import shapely.wkt
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.database import get_db
from src.models.property_models import Property, PropertyMedia, PropertyType, MediaType

router = APIRouter(prefix="/properties", tags=["properties"])

# --- Pydantic Schemas ---

class PropertyMediaBase(BaseModel):
    media_type: MediaType
    url: str
    order: int = 0

class PropertyMediaCreate(PropertyMediaBase):
    pass

class PropertyMediaResponse(PropertyMediaBase):
    id: int
    property_id: int
    model_config = ConfigDict(from_attributes=True)

class PropertyBase(BaseModel):
    type: PropertyType
    address: str
    price: float
    area_sqm: float
    rooms: int
    floor: Optional[int] = None
    year_built: Optional[int] = None

class PropertyCreate(PropertyBase):
    latitude: float
    longitude: float

class PropertyResponse(PropertyBase):
    id: int
    latitude: float
    longitude: float
    media: List[PropertyMediaResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- API Endpoints ---

@router.post("", response_model=PropertyResponse)
async def create_property(prop: PropertyCreate, db: AsyncSession = Depends(get_db)):
    # Create point geometry from lat/lon (WKT format)
    wkt_location = f"POINT({prop.longitude} {prop.latitude})"

    db_prop = Property(
        type=prop.type,
        address=prop.address,
        location=wkt_location,
        price=prop.price,
        area_sqm=prop.area_sqm,
        rooms=prop.rooms,
        floor=prop.floor,
        year_built=prop.year_built
    )
    db.add(db_prop)
    await db.commit()
    await db.refresh(db_prop)

    # Manually construct response to include lat/lon from input
    # (since converting back from DB location requires parsing)
    response = PropertyResponse(
        id=db_prop.id,
        type=db_prop.type,
        address=db_prop.address,
        price=db_prop.price,
        area_sqm=db_prop.area_sqm,
        rooms=db_prop.rooms,
        floor=db_prop.floor,
        year_built=db_prop.year_built,
        latitude=prop.latitude,
        longitude=prop.longitude,
        media=[]
    )
    return response

@router.get("", response_model=List[PropertyResponse])
async def list_properties(
    lat: Optional[float] = Query(None, description="Latitude for location filtering"),
    lon: Optional[float] = Query(None, description="Longitude for location filtering"),
    radius_km: Optional[float] = Query(None, description="Radius in kilometers"),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_area: Optional[float] = None,
    min_rooms: Optional[int] = None,
    type: Optional[PropertyType] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Property).options(selectinload(Property.media))

    if lat is not None and lon is not None and radius_km is not None:
        # Spatial filtering
        # Using degree approximation for simplicity with standard geometry (SRID 4326)
        # 1 degree approx 111.32 km
        radius_deg = radius_km / 111.32
        pt = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        query = query.where(func.ST_DWithin(Property.location, pt, radius_deg))

    if min_price is not None:
        query = query.where(Property.price >= min_price)
    if max_price is not None:
        query = query.where(Property.price <= max_price)
    if min_area is not None:
        query = query.where(Property.area_sqm >= min_area)
    if min_rooms is not None:
        query = query.where(Property.rooms >= min_rooms)
    if type is not None:
        query = query.where(Property.type == type)

    result = await db.execute(query)
    props = result.scalars().all()

    # Convert to response
    responses = []
    for p in props:
        latitude = 0.0
        longitude = 0.0
        if p.location is not None:
            if isinstance(p.location, WKBElement):
                shape = to_shape(p.location)
                latitude = shape.y
                longitude = shape.x
            elif isinstance(p.location, str):
                try:
                    shape = shapely.wkt.loads(p.location)
                    latitude = shape.y
                    longitude = shape.x
                except:
                    pass

        responses.append(PropertyResponse(
            id=p.id,
            type=p.type,
            address=p.address,
            price=p.price,
            area_sqm=p.area_sqm,
            rooms=p.rooms,
            floor=p.floor,
            year_built=p.year_built,
            latitude=latitude,
            longitude=longitude,
            media=[PropertyMediaResponse.model_validate(m) for m in p.media]
        ))

    return responses

@router.get("/{id}", response_model=PropertyResponse)
async def get_property(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Property).options(selectinload(Property.media)).where(Property.id == id))
    p = result.scalar_one_or_none()

    if not p:
        raise HTTPException(status_code=404, detail="Property not found")

    latitude = 0.0
    longitude = 0.0
    if p.location is not None:
        if isinstance(p.location, WKBElement):
            shape = to_shape(p.location)
            latitude = shape.y
            longitude = shape.x
        elif isinstance(p.location, str):
             try:
                shape = shapely.wkt.loads(p.location)
                latitude = shape.y
                longitude = shape.x
             except:
                pass

    return PropertyResponse(
        id=p.id,
        type=p.type,
        address=p.address,
        price=p.price,
        area_sqm=p.area_sqm,
        rooms=p.rooms,
        floor=p.floor,
        year_built=p.year_built,
        latitude=latitude,
        longitude=longitude,
        media=[PropertyMediaResponse.model_validate(m) for m in p.media]
    )

@router.post("/{id}/media", response_model=PropertyMediaResponse)
async def add_property_media(id: int, media: PropertyMediaCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Property).where(Property.id == id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    db_media = PropertyMedia(
        property_id=id,
        media_type=media.media_type,
        url=media.url,
        order=media.order
    )
    db.add(db_media)
    await db.commit()
    await db.refresh(db_media)
    return db_media
