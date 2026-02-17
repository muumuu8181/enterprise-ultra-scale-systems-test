from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from src.database import get_db
from src.models.space_models import Satellite, Telemetry, MissionCommand
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import math

router = APIRouter(prefix="/satellites", tags=["satellites"])

# Pydantic Models

class SatelliteResponse(BaseModel):
    id: int
    name: str
    orbit_type: str
    inclination: float
    altitude_km: float
    status: str
    model_config = ConfigDict(from_attributes=True)

class TelemetryResponse(BaseModel):
    id: int
    satellite_id: int
    timestamp: datetime
    position: Dict[str, float]
    velocity: Dict[str, float]
    battery_percent: float
    temperature_c: float
    anomalies: Optional[Any] = None
    model_config = ConfigDict(from_attributes=True)

class CommandCreate(BaseModel):
    command_type: str
    parameters: Dict[str, Any]
    scheduled_at: datetime

class CommandResponse(BaseModel):
    id: int
    satellite_id: int
    command_type: str
    parameters: Dict[str, Any]
    scheduled_at: datetime
    executed_at: Optional[datetime] = None
    result: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class OrbitPredictionResponse(BaseModel):
    satellite_id: int
    timestamp: datetime
    predicted_position: Dict[str, float]

# Endpoints

@router.get("/", response_model=List[SatelliteResponse])
async def get_satellites(db: AsyncSession = Depends(get_db)):
    """
    衛星一覧取得
    """
    result = await db.execute(select(Satellite))
    return result.scalars().all()

@router.get("/{satellite_id}/telemetry", response_model=List[TelemetryResponse])
async def get_satellite_telemetry(
    satellite_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    衛星テレメトリ取得
    """
    # 衛星存在確認
    sat_result = await db.execute(select(Satellite).where(Satellite.id == satellite_id))
    if not sat_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Satellite not found")

    stmt = select(Telemetry).where(Telemetry.satellite_id == satellite_id).order_by(desc(Telemetry.timestamp)).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/{satellite_id}/commands", response_model=CommandResponse, status_code=status.HTTP_201_CREATED)
async def create_mission_command(
    satellite_id: int,
    command: CommandCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    ミッションコマンド作成
    """
    # 衛星存在確認
    sat_result = await db.execute(select(Satellite).where(Satellite.id == satellite_id))
    if not sat_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Satellite not found")

    new_command = MissionCommand(
        satellite_id=satellite_id,
        command_type=command.command_type,
        parameters=command.parameters,
        scheduled_at=command.scheduled_at
    )
    db.add(new_command)
    await db.commit()
    await db.refresh(new_command)
    return new_command

@router.get("/{satellite_id}/orbit-prediction", response_model=List[OrbitPredictionResponse])
async def get_orbit_prediction(
    satellite_id: int,
    hours: int = Query(24, ge=1, le=72),
    db: AsyncSession = Depends(get_db)
):
    """
    軌道予測 (モック実装)
    """
    # 衛星存在確認
    sat_result = await db.execute(select(Satellite).where(Satellite.id == satellite_id))
    satellite = sat_result.scalar_one_or_none()
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")

    predictions = []
    base_time = datetime.utcnow()

    # 簡易的な予測（実際はTLEなどから計算が必要）
    # ここでは1時間ごとにダミーデータを返す
    for i in range(hours):
        future_time = base_time + timedelta(hours=i+1)
        # 単純な円運動を仮定したダミー座標
        angle = (future_time.timestamp() % 5400) / 5400 * 2 * math.pi # 90分周期と仮定
        r = satellite.altitude_km + 6371 # 地球半径 + 高度

        predictions.append(OrbitPredictionResponse(
            satellite_id=satellite_id,
            timestamp=future_time,
            predicted_position={
                "x": r * math.cos(angle),
                "y": r * math.sin(angle),
                "z": 0.0
            }
        ))

    return predictions
