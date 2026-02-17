from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import JSON
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import enum

class DisasterType(str, enum.Enum):
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    FIRE = "fire"

class DisasterEvent(Base):
    """
    災害イベントモデル
    """
    __tablename__ = "disaster_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[DisasterType] = mapped_column(Enum(DisasterType))
    severity: Mapped[str] = mapped_column(String) # low, medium, high, critical
    # 影響範囲エリア (POLYGON)
    affected_area: Mapped[Any] = mapped_column(Geometry("POLYGON", srid=4326))
    status: Mapped[str] = mapped_column(String, default="active") # active, resolved, closed
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    evacuation_routes: Mapped[List["EvacuationRoute"]] = relationship("EvacuationRoute", back_populates="event", cascade="all, delete-orphan")

class EvacuationRoute(Base):
    """
    避難経路モデル
    """
    __tablename__ = "evacuation_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("disaster_events.id"))
    # 経路情報 (GeoJSON形式)
    route_geojson: Mapped[Dict[str, Any]] = mapped_column(JSON)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    estimated_time_min: Mapped[int] = mapped_column(Integer)
    # 関連する避難所IDリスト
    shelter_ids: Mapped[List[int]] = mapped_column(JSON, default=list)

    event: Mapped["DisasterEvent"] = relationship("DisasterEvent", back_populates="evacuation_routes")

class Shelter(Base):
    """
    避難所モデル
    """
    __tablename__ = "shelters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    # 避難所位置 (POINT)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    capacity: Mapped[int] = mapped_column(Integer)
    current_occupancy: Mapped[int] = mapped_column(Integer, default=0)
    facilities: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict) # e.g. {"wifi": true, "medical": true}
