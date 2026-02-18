from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.elements import WKTElement

from src.models.v2x_models import CAMMessage, DENMMessage, SPATMessage
from src.services.v2x_message_handler import V2XMessageHandler
from src.services.glosa_calculator import GLOSACalculator
from src.services.pki_manager import PKIManager

router = APIRouter(prefix="/v2x", tags=["v2x"])

# Dependency Injection (本来はdependencies.pyなどで定義)
async def get_db():
    # 実際のDB接続ロジックが必要だが、ここではモックまたはプレースホルダー
    yield None

# Serviceのインスタンス化 (シングルトン推奨だが簡易的にここで生成)
pki_manager = PKIManager()
v2x_handler = V2XMessageHandler(pki_manager)
glosa_calculator = GLOSACalculator()

@router.post("/cam")
async def receive_cam(
    message: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    CAMメッセージを受信・処理する。
    """
    # 生データのデコード (ここではJSONで来ると仮定、またはBase64 encoded bytes)
    # 簡易的にmessage自体がデコード済みデータとして扱う

    # DBへの保存 (dbセッションがある場合)
    if db:
        cam = CAMMessage(
            vehicle_id=str(message.get("station_id")),
            station_id=message.get("station_id"),
            latitude=message.get("latitude"),
            longitude=message.get("longitude"),
            speed=message.get("speed"),
            heading=message.get("heading"),
            timestamp=datetime.now(timezone.utc),
            raw_bytes=str(message).encode('utf-8')
        )
        db.add(cam)
        await db.commit()

    # 周辺車両へのブロードキャスト
    await v2x_handler.broadcast_to_nearby_vehicles(
        message,
        message.get("latitude"),
        message.get("longitude")
    )

    return {"status": "received"}

@router.post("/denm")
async def receive_denm(
    message: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    DENMメッセージを受信する (危険情報配信)。
    """
    if db:
        # POINT(lon lat)
        loc = WKTElement(f"POINT({message.get('longitude')} {message.get('latitude')})", srid=4326)

        denm = DENMMessage(
            origin_station_id=message.get("origin_station_id"),
            cause_code=message.get("cause_code"),
            sub_cause_code=message.get("sub_cause_code"),
            location=loc,
            validity_duration=message.get("validity_duration"),
            created_at=datetime.now(timezone.utc)
        )
        db.add(denm)
        await db.commit()

    # ブロードキャスト (広範囲)
    await v2x_handler.broadcast_to_nearby_vehicles(
        message,
        message.get("latitude"),
        message.get("longitude"),
        radius_m=2000.0
    )
    return {"status": "received"}

@router.get("/denm/active")
async def get_active_denms(
    lat: float = Query(...),
    lon: float = Query(...),
    radius: float = Query(1000.0),
    db: AsyncSession = Depends(get_db)
):
    """
    周辺のアクティブなDENMを取得する。
    """
    if not db:
        return [] # DBがない場合は空リスト

    # PostGISのST_DWithinなどを使用して検索するクエリ (イメージ)
    # stmt = select(DENMMessage).where(
    #     func.ST_DWithin(DENMMessage.location, WKTElement(f"POINT({lon} {lat})", srid=4326), radius)
    # )
    # result = await db.execute(stmt)
    # return result.scalars().all()

    return []

@router.post("/spat")
async def receive_spat(
    message: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    SPATメッセージを受信する (信号情報)。
    """
    if db:
        spat = SPATMessage(
            intersection_id=message.get("intersection_id"),
            phase_states=message.get("phase_states"),
            timing_info=message.get("timing_info"),
            timestamp=datetime.now(timezone.utc)
        )
        db.add(spat)
        await db.commit()

    return {"status": "received"}

@router.get("/spat/{intersection_id}")
async def get_latest_spat(
    intersection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    最新のSPAT情報を取得する。
    """
    if not db:
        return {}

    # stmt = select(SPATMessage).where(SPATMessage.intersection_id == intersection_id).order_by(SPATMessage.timestamp.desc()).limit(1)
    # ...
    return {}

@router.post("/glosa/{intersection_id}")
async def calculate_glosa(
    intersection_id: int,
    vehicle_data: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    GLOSA推奨速度を計算する。
    """
    # 最新のSPATを取得 (モック)
    # spat = await get_latest_spat(intersection_id, db)
    spat = {
        "phase_states": {"1": "RED"},
        "timing_info": {"1": {"next_change": 15.0}} # 15秒後に変わる
    }

    current_phase = spat["phase_states"].get("1", "RED") # 仮のフェーズID
    time_to_change = spat["timing_info"].get("1", {}).get("next_change", 0.0)

    distance = vehicle_data.get("distance_to_intersection", 200.0)
    speed = vehicle_data.get("current_speed", 10.0)

    advisory_speed = glosa_calculator.calculate_advisory_speed(
        distance, speed, current_phase, time_to_change
    )

    return {
        "intersection_id": intersection_id,
        "advisory_speed": advisory_speed,
        "current_phase": current_phase
    }
