from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.elements import WKTElement
from src.database import get_db
from src.models.lighting_models import LightPole, LightingZone
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/lighting", tags=["lighting"])

# Schemas
class LightPoleCreate(BaseModel):
    pole_id: str
    latitude: float
    longitude: float
    zone_id: Optional[str] = None

class LightPoleResponse(BaseModel):
    id: int
    pole_id: str
    brightness: int
    status: str
    last_maintenance: datetime
    zone_id: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class BrightnessUpdate(BaseModel):
    level: int # 0-100

class ScheduleUpdate(BaseModel):
    schedule: Dict[str, Any]

class MotionTriggerUpdate(BaseModel):
    enabled: bool

# Endpoints

@router.post("/poles", response_model=LightPoleResponse)
async def create_pole(pole: LightPoleCreate, db: AsyncSession = Depends(get_db)):
    """
    街路灯登録 (テスト用)
    """
    point = f"POINT({pole.longitude} {pole.latitude})"
    db_pole = LightPole(
        pole_id=pole.pole_id,
        location=WKTElement(point, srid=4326),
        zone_id=pole.zone_id,
        brightness=0,
        status="active",
        last_maintenance=datetime.utcnow()
    )
    db.add(db_pole)
    try:
        await db.commit()
        await db.refresh(db_pole)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return db_pole

@router.get("/poles", response_model=List[LightPoleResponse])
async def get_poles(zone_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """
    街路灯一覧取得
    """
    query = select(LightPole)
    if zone_id:
        query = query.where(LightPole.zone_id == zone_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.put("/poles/{pole_id}/brightness")
async def set_brightness(
    pole_id: int,
    update: BrightnessUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    街路灯の明るさ設定 (0-100)
    """
    if not (0 <= update.level <= 100):
        raise HTTPException(status_code=400, detail="Brightness must be between 0 and 100")

    pole = await db.get(LightPole, pole_id)
    if not pole:
        raise HTTPException(status_code=404, detail="Light pole not found")

    pole.brightness = update.level
    await db.commit()
    return {"message": "Brightness updated", "level": pole.brightness}

@router.post("/zones/{zone_id}/schedule")
async def set_zone_schedule(
    zone_id: str,
    schedule_data: ScheduleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    ゾーンごとの照明スケジュール設定
    """
    # ゾーンが存在するか確認、なければ作成 (Upsert的挙動)
    query = select(LightingZone).where(LightingZone.zone_id == zone_id)
    result = await db.execute(query)
    zone = result.scalar_one_or_none()

    if not zone:
        zone = LightingZone(zone_id=zone_id)
        db.add(zone)

    zone.schedule = schedule_data.schedule
    zone.last_updated = datetime.utcnow()

    await db.commit()
    return {"message": "Schedule updated", "zone_id": zone_id}

@router.post("/zones/{zone_id}/motion-trigger")
async def set_motion_trigger(
    zone_id: str,
    trigger_data: MotionTriggerUpdate = Body(...), # Use Body explicitly if passing raw JSON bool or object
    db: AsyncSession = Depends(get_db)
):
    """
    人感センサー連動設定
    """
    query = select(LightingZone).where(LightingZone.zone_id == zone_id)
    result = await db.execute(query)
    zone = result.scalar_one_or_none()

    if not zone:
        # Create zone if it doesn't exist? Or 404?
        # Usually settings should be on existing zones, but for flexibility let's create.
        zone = LightingZone(zone_id=zone_id)
        db.add(zone)

    zone.motion_trigger_enabled = trigger_data.enabled
    zone.last_updated = datetime.utcnow()

    await db.commit()
    return {"message": "Motion trigger updated", "enabled": zone.motion_trigger_enabled}
