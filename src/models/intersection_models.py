from datetime import datetime
from sqlalchemy import Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from src.models.v2x_models import Base, utcnow

class IntersectionReservation(Base):
    """
    交差点予約モデル

    Attributes:
        id (int): 予約ID
        intersection_id (int): 交差点ID
        vehicle_id (str): 車両ID
        slot_start (datetime): 予約開始時刻
        slot_end (datetime): 予約終了時刻
        speed (float): 速度 (m/s)
        heading (float): 進行方向 (度)
        priority (bool): 優先度 (False: 通常, True: 緊急車両)
        created_at (datetime): 作成日時
    """
    __tablename__ = "intersection_reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    intersection_id: Mapped[int] = mapped_column(Integer, index=True)
    vehicle_id: Mapped[str] = mapped_column(String, index=True)
    slot_start: Mapped[datetime] = mapped_column(DateTime)
    slot_end: Mapped[datetime] = mapped_column(DateTime)
    speed: Mapped[float] = mapped_column(Float)
    heading: Mapped[float] = mapped_column(Float)
    priority: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
