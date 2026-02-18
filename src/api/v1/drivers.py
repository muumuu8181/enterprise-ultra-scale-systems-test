from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.database import get_db
from src.models.driver_models import Driver, DriverEarning, DriverStatus, VehicleType, DeliveryRoute
from src.services.dispatch_service import DispatchService
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date
# from geoalchemy2.shape import from_shape, to_shape # Not strictly needed if we don't return geometry in response or handle it manually
# from shapely.geometry import Point

router = APIRouter()

# --- Schemas ---

class DriverLocationUpdate(BaseModel):
    latitude: float
    longitude: float

class DriverStatusUpdate(BaseModel):
    status: DriverStatus

class EarningResponse(BaseModel):
    id: int
    driver_id: int
    date: date
    deliveries_count: int
    base_pay: float
    tips: float
    bonuses: float
    net_earnings: float

    model_config = ConfigDict(from_attributes=True)

class DeliveryHistoryItem(BaseModel):
    id: int
    order_id: int
    distance_km: float
    estimated_min: float
    actual_duration_min: Optional[float]

    model_config = ConfigDict(from_attributes=True)

# --- Endpoints ---

@router.post("/drivers/go-online")
async def go_online(
    driver_id: int,
    status_update: DriverStatusUpdate = DriverStatusUpdate(status=DriverStatus.online),
    db: AsyncSession = Depends(get_db)
):
    """
    Sets the driver status to online (or other status).
    """
    stmt = select(Driver).where(Driver.id == driver_id)
    result = await db.execute(stmt)
    driver = result.scalar_one_or_none()

    if not driver:
        # For testing purposes, if driver doesn't exist, we might want to create one or fail.
        # Failing is correct.
        raise HTTPException(status_code=404, detail="Driver not found")

    driver.status = status_update.status
    await db.commit()
    await db.refresh(driver)
    return {"status": "success", "new_status": driver.status}

@router.post("/drivers/update-location")
async def update_location(
    driver_id: int,
    location: DriverLocationUpdate,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Driver).where(Driver.id == driver_id)
    result = await db.execute(stmt)
    driver = result.scalar_one_or_none()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Update location using WKT format for PostGIS
    # Note: simple string assignment works with GeoAlchemy2 if configured,
    # but explicit WKT is safer.
    driver.current_location = f'POINT({location.longitude} {location.latitude})'

    await db.commit()
    return {"status": "success", "location": {"lat": location.latitude, "lon": location.longitude}}

@router.get("/drivers/{id}/earnings", response_model=List[EarningResponse])
async def get_earnings(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(DriverEarning).where(DriverEarning.driver_id == id)
    result = await db.execute(stmt)
    earnings = result.scalars().all()
    return earnings

@router.get("/drivers/{id}/delivery-history", response_model=List[DeliveryHistoryItem])
async def get_delivery_history(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(DeliveryRoute).where(DeliveryRoute.driver_id == id)
    result = await db.execute(stmt)
    history = result.scalars().all()
    return history

@router.post("/orders/{id}/pickup-confirm")
async def pickup_confirm(id: int, driver_id: int, db: AsyncSession = Depends(get_db)):
    # 'id' here represents the order_id as per URL path convention usually,
    # or the prompt implies POST /orders/{order_id}/...

    stmt = select(DeliveryRoute).where(DeliveryRoute.order_id == id, DeliveryRoute.driver_id == driver_id)
    result = await db.execute(stmt)
    route = result.scalar_one_or_none()

    if not route:
        # In a real app we might create a route or check order status.
        # For this exercise, return 404 if route not pre-assigned.
        raise HTTPException(status_code=404, detail="Route not found for this order")

    return {"status": "picked_up", "order_id": id}

@router.post("/orders/{id}/delivery-confirm")
async def delivery_confirm(id: int, driver_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(DeliveryRoute).where(DeliveryRoute.order_id == id, DeliveryRoute.driver_id == driver_id)
    result = await db.execute(stmt)
    route = result.scalar_one_or_none()

    if not route:
        raise HTTPException(status_code=404, detail="Route not found for this order")

    return {"status": "delivered", "order_id": id}
