from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape
import json

from src.models.fleet_models import Fleet, FleetVehicle, FleetTask, Vehicle
from src.services.fleet_optimizer import FleetOptimizer
from src.core.database import get_db

router = APIRouter(prefix="/fleet", tags=["fleet"])
optimizer = FleetOptimizer()

# --- Pydantic Models ---

class VehicleCreateRequest(BaseModel):
    fleet_id: int
    vehicle_id: str
    model: str
    purpose: str = Field(..., description="車両の用途")

class VehicleResponse(BaseModel):
    id: int
    fleet_id: int
    vehicle_id: str
    model: str
    status: str
    location: Optional[dict] = None # {lat, lon}

    model_config = ConfigDict(from_attributes=True)

class TaskCreateRequest(BaseModel):
    vehicle_id: str = Field(..., description="車両ID (必須)")
    task_type: str
    destination: dict = Field(..., description="{'lat': float, 'lon': float}")
    priority: int

class TaskStatusResponse(BaseModel):
    id: int
    status: str
    vehicle_id: Optional[int]
    assigned_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class AnalyticsResponse(BaseModel):
    fleet_id: int
    generated_at: datetime
    total_vehicles: int
    total_distance_km: float
    estimated_fuel_consumption_liters: float
    total_idling_hours: float
    status: str

# --- Endpoints ---

@router.post("/vehicles", response_model=VehicleResponse)
async def register_vehicle(
    vehicle_in: VehicleCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    フリートに車両を登録する
    """
    # Note: 実際には fleet_id の存在確認などが必要
    # purposeフィールドはDBスキーマに含まれていないため、現在はstatus初期値等には使用せず、無視する。
    # 必要であればスキーマ変更を検討するが、要件に従いstatusはデフォルト'active'とする。
    new_vehicle = FleetVehicle(
        fleet_id=vehicle_in.fleet_id,
        vehicle_id=vehicle_in.vehicle_id,
        model=vehicle_in.model,
        status="active"
    )
    db.add(new_vehicle)
    try:
        await db.commit()
        await db.refresh(new_vehicle)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Vehicle ID or Fleet ID invalid, or Vehicle already registered.")

    return new_vehicle

@router.get("/{fleet_id}/vehicles", response_model=List[VehicleResponse])
async def list_vehicles(
    fleet_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    全車両一覧 (リアルタイム位置含む)
    """
    stmt = (
        select(FleetVehicle, Vehicle)
        .join(Vehicle, FleetVehicle.vehicle_id == Vehicle.id, isouter=True)
        .where(FleetVehicle.fleet_id == fleet_id)
    )
    result = await db.execute(stmt)
    rows = result.all()

    response = []
    for f_vehicle, vehicle in rows:
        loc = None
        # GeoAlchemy2 の location カラムから座標を取得
        if vehicle and vehicle.location is not None:
             try:
                 # to_shape converts WKBElement/WKTElement to shapely geometry
                 point = to_shape(vehicle.location)
                 # Shapely Point has x (lon) and y (lat)
                 loc = {"lat": point.y, "lon": point.x}
             except Exception:
                 # 変換エラー時はNoneとする
                 pass

        response.append(VehicleResponse(
            id=f_vehicle.id,
            fleet_id=f_vehicle.fleet_id,
            vehicle_id=f_vehicle.vehicle_id,
            model=f_vehicle.model,
            status=f_vehicle.status,
            location=loc
        ))
    return response

@router.get("/{fleet_id}/analytics", response_model=AnalyticsResponse)
async def get_fleet_analytics_endpoint(
    fleet_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    走行分析 (総走行距離, 燃費, アイドリング時間)
    """
    report = await optimizer.generate_fleet_report(db, fleet_id)
    return AnalyticsResponse(**report)

@router.post("/tasks", response_model=TaskStatusResponse)
async def create_task(
    task_in: TaskCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    タスクを作成 (vehicle_id, task_type, destination, priority)
    """
    lat = task_in.destination['lat']
    lon = task_in.destination['lon']
    point_wkt = WKTElement(f"POINT({lon} {lat})", srid=4326)

    # vehicle_id (str) から fleet_id と FleetVehicle.id を特定
    stmt = select(FleetVehicle).where(FleetVehicle.vehicle_id == task_in.vehicle_id)
    res = await db.execute(stmt)
    fv = res.scalar_one_or_none()

    if not fv:
        # 車両が見つからない場合のエラー
        raise HTTPException(status_code=404, detail=f"Vehicle {task_in.vehicle_id} not found in any fleet")

    fleet_id = fv.fleet_id
    vehicle_db_id = fv.id

    new_task = FleetTask(
        fleet_id=fleet_id,
        vehicle_id=vehicle_db_id,
        task_type=task_in.task_type,
        destination=point_wkt,
        priority=task_in.priority,
        status="pending",
        assigned_at=datetime.now() # 即時割り当てとみなす
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return TaskStatusResponse(
        id=new_task.id,
        status=new_task.status,
        vehicle_id=new_task.vehicle_id,
        assigned_at=new_task.assigned_at
    )

@router.get("/tasks/{id}/status", response_model=TaskStatusResponse)
async def get_task_status_endpoint(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    タスクステータス確認
    """
    stmt = select(FleetTask).where(FleetTask.id == id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        id=task.id,
        status=task.status,
        vehicle_id=task.vehicle_id,
        assigned_at=task.assigned_at
    )
