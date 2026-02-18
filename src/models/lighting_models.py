from sqlalchemy import Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.types import JSON
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import Any, Dict

class LightPole(Base):
    """
    街路灯モデル
    """
    __tablename__ = "light_poles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pole_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    # PostGISのPOINT型 (SRID 4326: WGS84)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    brightness: Mapped[int] = mapped_column(Integer, default=0) # 0-100
    status: Mapped[str] = mapped_column(String, default="active")
    last_maintenance: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    zone_id: Mapped[str] = mapped_column(String, index=True, nullable=True)

class LightingZone(Base):
    """
    照明ゾーン設定モデル
    """
    __tablename__ = "lighting_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    zone_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    schedule: Mapped[Dict[str, Any]] = mapped_column(JSON, default={})
    motion_trigger_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
