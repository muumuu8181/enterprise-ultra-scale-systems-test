from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from geoalchemy2.elements import WKTElement
from src.database import get_db
from src.models.city_models import TrafficSignal, Sensor
from src.services.traffic_controller import TrafficController
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/traffic", tags=["traffic"])
controller = TrafficController()

class TrafficSignalResponse(BaseModel):
    id: int
    intersection_id: str
    signal_group: str
    state: str
    cycle_time: int
    green_time: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SignalUpdate(BaseModel):
    cycle_time: int
    green_time: int

class OptimizeRequest(BaseModel):
    intersection_id: str
    current_flows: Dict[str, float]

@router.get("/signals/{intersection_id}", response_model=List[TrafficSignalResponse])
async def get_signal_state(intersection_id: str, db: AsyncSession = Depends(get_db)):
    """
    信号機状態取得
    """
    result = await db.execute(select(TrafficSignal).where(TrafficSignal.intersection_id == intersection_id))
    signals = result.scalars().all()
    if not signals:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signals

@router.put("/signals/{intersection_id}")
async def update_signal(intersection_id: str, update_data: SignalUpdate, db: AsyncSession = Depends(get_db)):
    """
    信号機更新 (cycle_time, green_time)
    """
    stmt = (
        update(TrafficSignal)
        .where(TrafficSignal.intersection_id == intersection_id)
        .values(cycle_time=update_data.cycle_time, green_time=update_data.green_time)
    )
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
         raise HTTPException(status_code=404, detail="Signal not found or no update needed")

    return {"message": "Signal updated", "intersection_id": intersection_id}

@router.post("/optimize")
async def optimize_traffic(request: OptimizeRequest):
    """
    Webster法による最適化
    """
    # Note: controller uses its own session management internally for DB updates
    # Usually better to pass session, but following existing structure
    result = await controller.optimize_intersection(request.intersection_id, request.current_flows)
    return result

@router.get("/heatmap")
async def get_traffic_heatmap(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    db: AsyncSession = Depends(get_db)
):
    """
    渋滞ヒートマップ
    bounds=min_lon,min_lat,max_lon,max_lat
    """
    # Bounding box polygon
    polygon = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"

    # Select sensors within bounds
    stmt = select(Sensor).where(
        func.ST_Within(
            func.CAST(Sensor.location, type_="geometry"),
            func.ST_GeomFromText(polygon, 4326)
        )
    )

    result = await db.execute(stmt)
    sensors = result.scalars().all()

    heatmap_data = []
    for s in sensors:
        # Get latest reading to determine "heat" (e.g., congestion level)
        # This part is simplified
        heatmap_data.append({
            "lat": 0, # Should extract from s.location
            "lon": 0,
            "intensity": 0.5
        })

    return heatmap_data
