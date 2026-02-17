from sqlalchemy import Integer, String, Float, DateTime
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.types import JSON
from src.database import Base
from datetime import datetime
from typing import Optional, List, Any

class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    origin: Mapped[str] = mapped_column(String)
    destination: Mapped[str] = mapped_column(String)
    waypoints: Mapped[List[Any]] = mapped_column(JSON, default=list)
    distance_km: Mapped[float] = mapped_column(Float)
    duration_min: Mapped[float] = mapped_column(Float)
    route_polyline: Mapped[str] = mapped_column(String) # Encoded polyline or JSON string
    transport_mode: Mapped[str] = mapped_column(String) # driving/walking/transit

class TrafficSegment(Base):
    __tablename__ = "traffic_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    segment_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    road_name: Mapped[str] = mapped_column(String)
    current_speed_kmh: Mapped[float] = mapped_column(Float)
    free_flow_speed: Mapped[float] = mapped_column(Float)
    congestion_level: Mapped[int] = mapped_column(Integer) # 0-5

class ETARequest(Base):
    __tablename__ = "eta_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    origin: Mapped[str] = mapped_column(String)
    destination: Mapped[str] = mapped_column(String)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    estimated_arrival: Mapped[datetime] = mapped_column(DateTime)
    actual_arrival: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    mode: Mapped[str] = mapped_column(String)
