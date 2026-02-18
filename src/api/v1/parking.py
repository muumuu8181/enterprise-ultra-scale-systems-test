from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from geoalchemy2.elements import WKTElement
from src.database import get_db
from src.models.parking_models import ParkingLot, ParkingSpace, ParkingReservation
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/parking", tags=["parking"])

# Pydantic Models
class ParkingLotResponse(BaseModel):
    id: int
    name: str
    total_spaces: int
    available_spaces: int
    price_per_hour: float
    model_config = ConfigDict(from_attributes=True)

class ParkingSpaceResponse(BaseModel):
    id: int
    lot_id: int
    space_number: str
    is_occupied: bool
    is_handicapped: bool
    last_updated: datetime
    model_config = ConfigDict(from_attributes=True)

class ReservationCreate(BaseModel):
    lot_id: int
    start_time: datetime
    duration_minutes: int
    user_id: str # 簡易的にリクエストに含める

class ReservationResponse(BaseModel):
    id: int
    lot_id: int
    user_id: str
    space_id: int
    start_time: datetime
    end_time: datetime
    fee: float
    model_config = ConfigDict(from_attributes=True)

class GuidanceResponse(BaseModel):
    lot: ParkingLotResponse
    distance_meters: float

# Endpoints

@router.get("/lots", response_model=List[ParkingLotResponse])
async def get_parking_lots(db: AsyncSession = Depends(get_db)):
    """
    駐車場一覧取得 (空き状況含む)
    """
    result = await db.execute(select(ParkingLot))
    return result.scalars().all()

@router.get("/lots/{lot_id}/availability", response_model=int)
async def get_lot_availability(lot_id: int, db: AsyncSession = Depends(get_db)):
    """
    リアルタイム空き台数取得
    """
    # 実際の空きスペース数 (is_occupied=False) をカウント
    stmt = select(func.count(ParkingSpace.id)).where(
        and_(ParkingSpace.lot_id == lot_id, ParkingSpace.is_occupied == False)
    )
    result = await db.execute(stmt)
    count = result.scalar()

    # ParkingLotテーブルのavailable_spacesも更新しておくと整合性が取れるが、
    # ここでは計算値を返す
    return count if count is not None else 0

@router.post("/reservations", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(reservation: ReservationCreate, db: AsyncSession = Depends(get_db)):
    """
    駐車場予約作成
    """
    # 駐車場の存在確認
    lot_result = await db.execute(select(ParkingLot).where(ParkingLot.id == reservation.lot_id))
    lot = lot_result.scalar_one_or_none()
    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found")

    end_time = reservation.start_time + timedelta(minutes=reservation.duration_minutes)
    fee = (reservation.duration_minutes / 60.0) * lot.price_per_hour

    # 空きスペースを探す (単純化: 現在空いていて、予約重複がないスペース)
    # 本来は複雑な時間枠管理が必要だが、ここでは簡易実装
    stmt = select(ParkingSpace).where(
        and_(
            ParkingSpace.lot_id == reservation.lot_id,
            ParkingSpace.is_occupied == False
            # 本来は既存予約との重複チェックが必要
            # ~exists(select(ParkingReservation).where(...))
        )
    )
    result = await db.execute(stmt)
    space = result.scalars().first()

    if not space:
        raise HTTPException(status_code=409, detail="No available spaces")

    new_reservation = ParkingReservation(
        lot_id=reservation.lot_id,
        user_id=reservation.user_id,
        space_id=space.id,
        start_time=reservation.start_time,
        end_time=end_time,
        fee=fee
    )
    db.add(new_reservation)

    # スペースを埋める処理は、予約開始時刻になったら行われるべきだが、
    # 簡易的に今すぐ埋めるか、あるいは予約テーブルだけで管理するか。
    # ここでは予約レコード作成のみとする。

    await db.commit()
    await db.refresh(new_reservation)
    return new_reservation

@router.post("/payments/{reservation_id}")
async def process_payment(reservation_id: int, db: AsyncSession = Depends(get_db)):
    """
    駐車料金支払い (モック)
    """
    stmt = select(ParkingReservation).where(ParkingReservation.id == reservation_id)
    result = await db.execute(stmt)
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    # ここで決済処理を行う想定

    return {"message": "Payment successful", "reservation_id": reservation_id, "amount": reservation.fee}

@router.get("/guidance", response_model=List[GuidanceResponse])
async def parking_guidance(destination: str, db: AsyncSession = Depends(get_db)):
    """
    最寄り空き駐車場案内
    destination: "lat,lon" (例: 35.6895,139.6917)
    """
    try:
        lat_str, lon_str = destination.split(',')
        lat = float(lat_str)
        lon = float(lon_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid destination format. Use 'lat,lon'")

    # 現在地(destination)からの距離でソートし、空きがあるものを返す
    # PostGISのST_Distance_Sphere (またはST_Distance) を使用
    # locationは Geometry(POINT, 4326)

    user_location = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

    # 距離計算 (メートル単位には本来 geography型か ST_DistanceSphere 推奨だが、ここでは簡易的に geometry で計算し、度単位の距離が出るので注意が必要。
    # ただし GeoAlchemy2 の ST_Distance は geometry 同士だとデカルト距離。
    # 日本付近では 1度 ≒ 111km。
    # 正確には geography castするか ST_DistanceSphere を使う。
    # ここでは ST_DistanceSphere を使う。

    stmt = select(ParkingLot, func.ST_DistanceSphere(ParkingLot.location, user_location).label("distance")) \
        .where(ParkingLot.available_spaces > 0) \
        .order_by("distance") \
        .limit(5)

    result = await db.execute(stmt)
    rows = result.all()

    response = []
    for row in rows:
        lot = row[0]
        dist = row[1]
        response.append(GuidanceResponse(lot=ParkingLotResponse.model_validate(lot), distance_meters=dist))

    return response
