from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import List, Any

class ParkingLot(Base):
    """
    駐車場モデル
    """
    __tablename__ = "parking_lots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    # PostGISのPOINT型 (SRID 4326: WGS84)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    total_spaces: Mapped[int] = mapped_column(Integer)
    available_spaces: Mapped[int] = mapped_column(Integer, default=0)
    price_per_hour: Mapped[float] = mapped_column(Float)

    spaces: Mapped[List["ParkingSpace"]] = relationship("ParkingSpace", back_populates="lot", cascade="all, delete-orphan")
    reservations: Mapped[List["ParkingReservation"]] = relationship("ParkingReservation", back_populates="lot", cascade="all, delete-orphan")

class ParkingSpace(Base):
    """
    駐車スペースモデル
    """
    __tablename__ = "parking_spaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("parking_lots.id"))
    space_number: Mapped[str] = mapped_column(String)
    is_occupied: Mapped[bool] = mapped_column(Boolean, default=False)
    is_handicapped: Mapped[bool] = mapped_column(Boolean, default=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lot: Mapped["ParkingLot"] = relationship("ParkingLot", back_populates="spaces")
    reservations: Mapped[List["ParkingReservation"]] = relationship("ParkingReservation", back_populates="space")

class ParkingReservation(Base):
    """
    駐車場予約モデル
    """
    __tablename__ = "parking_reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("parking_lots.id"))
    user_id: Mapped[str] = mapped_column(String) # ユーザーID (外部システム連携を想定しString)
    space_id: Mapped[int] = mapped_column(Integer, ForeignKey("parking_spaces.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    fee: Mapped[float] = mapped_column(Float)

    # 支払い済みかどうかを追加 (要件にはないが実用的) -> 要件厳守のため追加しないが、payments APIでどうにかする
    # payments APIはMockなのでDB変更なしでOKとするか、statusを追加するか。
    # ここでは要件通りのフィールドにする。

    lot: Mapped["ParkingLot"] = relationship("ParkingLot", back_populates="reservations")
    space: Mapped["ParkingSpace"] = relationship("ParkingSpace", back_populates="reservations")
