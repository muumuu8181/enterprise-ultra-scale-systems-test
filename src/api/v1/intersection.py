from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from pydantic import BaseModel, Field, ConfigDict

from src.services.intersection_manager import IntersectionManager
from src.models.intersection_models import IntersectionReservation

# Dependency injection placeholder
async def get_db():
    yield None

router = APIRouter(prefix="/intersection", tags=["intersection"])
manager = IntersectionManager()

class VehicleEnterRequest(BaseModel):
    vehicle_id: str
    speed: float
    heading: float

class ReservationRequest(BaseModel):
    vehicle_id: str
    arrival_time: datetime
    speed: float = 10.0
    heading: float = 0.0
    duration_seconds: float = 2.0
    priority: bool = False

class ReservationResponse(BaseModel):
    id: int
    intersection_id: int
    vehicle_id: str
    slot_start: datetime
    slot_end: datetime
    priority: bool

    model_config = ConfigDict(from_attributes=True)

@router.post("/{id}/vehicles/enter")
async def vehicle_enter(
    id: int = Path(..., description="Intersection ID"),
    req: VehicleEnterRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    車両の交差点接近通知。
    """
    # 実際にはここで位置情報の更新や、即時の危険判定などを行う。
    # 今回はログ出力のみ。
    print(f"Vehicle {req.vehicle_id} entering intersection {id} at speed {req.speed}, heading {req.heading}")
    return {"status": "notified", "intersection_id": id, "vehicle_id": req.vehicle_id}

@router.get("/{id}/reservation/slots", response_model=List[ReservationResponse])
async def get_reservation_slots(
    id: int = Path(..., description="Intersection ID"),
    mode: str = Query("fcfs", description="Scheduling mode: fcfs or priority"),
    db: AsyncSession = Depends(get_db)
):
    """
    予約済みスロットの一覧を取得する。
    """
    if not db:
        return []

    if mode == "priority":
        reservations = await manager.implement_priority(db, id)
    else:
        reservations = await manager.implement_fcfs(db, id)

    return reservations

@router.post("/{id}/reservation", response_model=ReservationResponse)
async def make_reservation(
    id: int = Path(..., description="Intersection ID"),
    req: ReservationRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    交差点通過の予約を行う。
    """
    if not db:
        raise HTTPException(status_code=500, detail="Database not available")

    reservation = await manager.reserve_slot(
        db,
        intersection_id=id,
        vehicle_id=req.vehicle_id,
        arrival_time=req.arrival_time,
        duration_seconds=req.duration_seconds,
        speed=req.speed,
        heading=req.heading,
        priority=req.priority
    )

    if not reservation:
        raise HTTPException(status_code=409, detail="Slot conflict or reservation failed")

    return reservation

@router.delete("/{id}/reservation/{res_id}")
async def cancel_reservation(
    id: int = Path(..., description="Intersection ID"),
    res_id: int = Path(..., description="Reservation ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    予約をキャンセルする。
    """
    if not db:
        raise HTTPException(status_code=500, detail="Database not available")

    # 指定された交差点IDの予約IDであるかを確認して削除
    stmt = delete(IntersectionReservation).where(
        IntersectionReservation.id == res_id,
        IntersectionReservation.intersection_id == id
    )
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
         raise HTTPException(status_code=404, detail="Reservation not found")

    return {"status": "cancelled", "id": res_id}
