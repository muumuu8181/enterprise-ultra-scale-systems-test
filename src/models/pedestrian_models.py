from datetime import datetime
from typing import Any
from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from src.models.base import Base, utcnow

class PedestrianDevice(Base):
    """
    歩行者デバイス情報を管理するモデル
    スマートフォンやウェアラブルデバイスからの情報を保持

    Attributes:
        id (int): 内部ID
        device_id (str): デバイス識別子
        device_type (str): デバイスタイプ (smartphone/wearable)
        location (Geometry): 現在位置 (POINT)
        speed (float): 速度 (m/s)
        heading (float): 進行方向 (度)
        updated_at (datetime): 更新日時
    """
    __tablename__ = "pedestrian_devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    device_type: Mapped[str] = mapped_column(String)
    # PostGISのPOINT型を使用 (SRID 4326: WGS84)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    speed: Mapped[float] = mapped_column(Float, default=0.0)
    heading: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

class SafetyAlert(Base):
    """
    安全アラート履歴モデル
    車両と歩行者の接近検知ログ

    Attributes:
        id (int): アラートID
        vehicle_id (str): 車両ID
        pedestrian_id (str): 歩行者デバイスID
        ttc_seconds (float): 衝突余裕時間 (秒)
        distance_m (float): 距離 (m)
        created_at (datetime): 作成日時
    """
    __tablename__ = "safety_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(String, index=True)
    pedestrian_id: Mapped[str] = mapped_column(String, index=True)
    ttc_seconds: Mapped[float] = mapped_column(Float)
    distance_m: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
