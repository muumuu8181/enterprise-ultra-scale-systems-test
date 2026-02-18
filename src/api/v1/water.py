from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.elements import WKTElement
from src.database import get_db
from src.models.water_models import WaterPressureSensor, WaterLeak, WaterQualityReading
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/water", tags=["water"])

# Schemas
class WaterPressureResponse(BaseModel):
    id: int
    zone_id: str
    pressure_bar: float
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class LeakReportCreate(BaseModel):
    latitude: float
    longitude: float
    severity: str
    estimated_loss_liters: Optional[float] = None

class LeakResponse(BaseModel):
    id: int
    severity: str
    reported_at: datetime
    repaired_at: Optional[datetime]
    estimated_loss_liters: Optional[float]
    model_config = ConfigDict(from_attributes=True)

class WaterQualityResponse(BaseModel):
    id: int
    station_id: str
    ph: float
    turbidity: float
    chlorine_residual: float
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class ValveControlRequest(BaseModel):
    action: str # open/close/partial

# Endpoints

@router.get("/pressure/{zone_id}", response_model=List[WaterPressureResponse])
async def get_pressure(zone_id: str, db: AsyncSession = Depends(get_db)):
    """
    水圧モニタリング
    """
    stmt = select(WaterPressureSensor).where(WaterPressureSensor.zone_id == zone_id).order_by(WaterPressureSensor.timestamp.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/leaks/report", response_model=LeakResponse)
async def report_leak(report: LeakReportCreate, db: AsyncSession = Depends(get_db)):
    """
    漏水報告
    """
    point = f"POINT({report.longitude} {report.latitude})"
    new_leak = WaterLeak(
        location=WKTElement(point, srid=4326),
        severity=report.severity,
        reported_at=datetime.utcnow(),
        estimated_loss_liters=report.estimated_loss_liters
    )
    db.add(new_leak)
    await db.commit()
    await db.refresh(new_leak)
    return new_leak

@router.get("/leaks/active", response_model=List[LeakResponse])
async def get_active_leaks(db: AsyncSession = Depends(get_db)):
    """
    アクティブな漏水一覧
    """
    stmt = select(WaterLeak).where(WaterLeak.repaired_at.is_(None)).order_by(WaterLeak.reported_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/quality/{station_id}", response_model=List[WaterQualityResponse])
async def get_quality(station_id: str, db: AsyncSession = Depends(get_db)):
    """
    水質データ取得
    """
    stmt = select(WaterQualityReading).where(WaterQualityReading.station_id == station_id).order_by(WaterQualityReading.timestamp.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/valve/{valve_id}/control")
async def control_valve(valve_id: str, request: ValveControlRequest):
    """
    バルブ制御 (open/close/partial)
    """
    valid_actions = ["open", "close", "partial"]
    if request.action not in valid_actions:
         raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of {valid_actions}")

    # 実際はIoTデバイスへのコマンド送信などを行う
    # ここでは成功応答のみ返す
    return {"message": f"Valve {valve_id} control command sent", "action": request.action, "status": "success"}
