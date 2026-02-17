from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.elements import WKTElement
from src.database import get_db
from src.models.disaster_models import DisasterEvent, EvacuationRoute, Shelter, DisasterType
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

router = APIRouter(prefix="/disaster", tags=["disaster"])

# --- Schemas ---

class DisasterEventCreate(BaseModel):
    """
    災害イベント作成用スキーマ
    """
    type: DisasterType
    severity: str
    area_polygon: str = Field(..., description="WKT形式のポリゴン文字列 (例: 'POLYGON(...)')")

class DisasterEventResponse(BaseModel):
    """
    災害イベントレスポンス用スキーマ
    """
    id: int
    type: DisasterType
    severity: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    # Geometryのシリアライズは複雑なため、ここでは省略するか、必要な場合は別途処理が必要
    # Pydanticのfrom_attributes=TrueだけではWKTElementなどを自動変換できない場合がある
    # ここではシンプルにIDなどを返す

    model_config = ConfigDict(from_attributes=True)

class EvacuationRouteCreate(BaseModel):
    """
    避難経路作成用スキーマ
    """
    event_id: int
    route_geojson: Dict[str, Any]
    priority: int = 1
    estimated_time_min: int
    shelter_ids: List[int] = Field(default_factory=list)

class EvacuationRouteResponse(BaseModel):
    """
    避難経路レスポンス用スキーマ
    """
    id: int
    event_id: int
    route_geojson: Dict[str, Any]
    priority: int
    estimated_time_min: int
    shelter_ids: List[int]

    model_config = ConfigDict(from_attributes=True)

class ShelterCreate(BaseModel):
    """
    避難所作成用スキーマ (テスト・管理用)
    """
    name: str
    latitude: float
    longitude: float
    capacity: int
    facilities: Dict[str, Any] = Field(default_factory=dict)

class ShelterResponse(BaseModel):
    """
    避難所レスポンス用スキーマ
    """
    id: int
    name: str
    capacity: int
    current_occupancy: int
    facilities: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class OccupancyUpdate(BaseModel):
    """
    避難所人数更新用スキーマ
    """
    count: int

# --- Endpoints ---

@router.post("/events", response_model=DisasterEventResponse)
async def create_event(event: DisasterEventCreate, db: AsyncSession = Depends(get_db)):
    """
    新規災害イベントを作成する
    """
    # WKT形式のポリゴンを作成
    polygon = WKTElement(event.area_polygon, srid=4326)

    db_event = DisasterEvent(
        type=event.type,
        severity=event.severity,
        affected_area=polygon,
        status="active",
        started_at=datetime.now(timezone.utc)
    )
    db.add(db_event)
    try:
        await db.commit()
        await db.refresh(db_event)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create event: {str(e)}")

    return db_event

@router.get("/events/active", response_model=List[DisasterEventResponse])
async def get_active_events(db: AsyncSession = Depends(get_db)):
    """
    現在アクティブな災害イベント一覧を取得する
    """
    query = select(DisasterEvent).where(DisasterEvent.status == "active")
    result = await db.execute(query)
    events = result.scalars().all()
    return events

@router.post("/evacuations", response_model=EvacuationRouteResponse)
async def create_evacuation_route(route: EvacuationRouteCreate, db: AsyncSession = Depends(get_db)):
    """
    避難経路を作成し、避難所と紐付ける
    """
    # イベントの存在確認
    event = await db.get(DisasterEvent, route.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Disaster event not found")

    db_route = EvacuationRoute(
        event_id=route.event_id,
        route_geojson=route.route_geojson,
        priority=route.priority,
        estimated_time_min=route.estimated_time_min,
        shelter_ids=route.shelter_ids
    )
    db.add(db_route)
    try:
        await db.commit()
        await db.refresh(db_route)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create evacuation route: {str(e)}")

    return db_route

@router.post("/shelters", response_model=ShelterResponse)
async def create_shelter(shelter: ShelterCreate, db: AsyncSession = Depends(get_db)):
    """
    避難所を登録する (管理用)
    """
    point = WKTElement(f"POINT({shelter.longitude} {shelter.latitude})", srid=4326)

    db_shelter = Shelter(
        name=shelter.name,
        location=point,
        capacity=shelter.capacity,
        current_occupancy=0,
        facilities=shelter.facilities
    )
    db.add(db_shelter)
    await db.commit()
    await db.refresh(db_shelter)
    return db_shelter

@router.get("/shelters", response_model=List[ShelterResponse])
async def get_shelters(db: AsyncSession = Depends(get_db)):
    """
    避難所一覧を取得する (定員、現在の収容人数を含む)
    """
    query = select(Shelter)
    result = await db.execute(query)
    shelters = result.scalars().all()
    return shelters

@router.put("/shelters/{id}/occupancy", response_model=ShelterResponse)
async def update_shelter_occupancy(
    id: int,
    update: OccupancyUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    避難所の収容人数を更新する
    """
    shelter = await db.get(Shelter, id)
    if not shelter:
        raise HTTPException(status_code=404, detail="Shelter not found")

    if update.count > shelter.capacity:
        # 定員オーバーでも記録はするか、エラーにするか。ここでは記録は許可するが、運用次第。
        # 今回はそのまま更新する。
        pass

    shelter.current_occupancy = update.count
    await db.commit()
    await db.refresh(shelter)
    return shelter
