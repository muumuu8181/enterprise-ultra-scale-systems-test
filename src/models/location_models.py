from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import JSON
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import Optional, Any, Dict, List

class UserLocation(Base):
    __tablename__ = "user_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    accuracy_m: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source: Mapped[str] = mapped_column(String) # gps/wifi/cell

    # Store Point geometry for spatial indexing
    geom: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))

class GeofenceZone(Base):
    __tablename__ = "geofence_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    # Support both Polygon and Point (for circles)
    geometry: Mapped[Any] = mapped_column(Geometry("GEOMETRY", srid=4326))
    zone_type: Mapped[str] = mapped_column(String) # circle/polygon
    trigger_on: Mapped[str] = mapped_column(String) # enter/exit/dwell
    dwell_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    radius_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # For circle type

    events: Mapped[List["GeofenceEvent"]] = relationship("GeofenceEvent", back_populates="zone", cascade="all, delete-orphan")

class GeofenceEvent(Base):
    __tablename__ = "geofence_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    zone_id: Mapped[int] = mapped_column(Integer, ForeignKey("geofence_zones.id"))
    event_type: Mapped[str] = mapped_column(String) # enter/exit/dwell
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata_info: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, nullable=True)

    zone: Mapped["GeofenceZone"] = relationship("GeofenceZone", back_populates="events")
