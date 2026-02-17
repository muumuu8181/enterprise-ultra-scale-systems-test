from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import Any

class NoiseReading(Base):
    """
    騒音読み取り値モデル
    """
    __tablename__ = "noise_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sensor_id: Mapped[int] = mapped_column(Integer, ForeignKey("sensors.id"), index=True)
    db_level: Mapped[float] = mapped_column(Float)
    frequency_hz: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class NoiseComplaint(Base):
    """
    騒音苦情モデル
    """
    __tablename__ = "noise_complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # PostGISのPOINT型 (SRID 4326: WGS84)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    db_level: Mapped[float] = mapped_column(Float) # ユーザー申告値または推定値
    description: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
