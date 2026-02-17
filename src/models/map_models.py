from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from src.core.database import Base
from datetime import datetime
from typing import Optional, List, Any

class MapNode(Base):
    __tablename__ = "map_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    location = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    node_type: Mapped[str] = mapped_column(String, nullable=False)  # intersection/endpoint
    elevation_m: Mapped[float] = mapped_column(Float, nullable=False)

class RoadSegment(Base):
    __tablename__ = "road_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    from_node: Mapped[int] = mapped_column(ForeignKey("map_nodes.id"), nullable=False)
    to_node: Mapped[int] = mapped_column(ForeignKey("map_nodes.id"), nullable=False)
    distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    speed_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    road_type: Mapped[str] = mapped_column(String, nullable=False)
    geometry = mapped_column(Geometry("LINESTRING", srid=4326), nullable=False)

    # Relationships
    source_node = relationship("MapNode", foreign_keys=[from_node])
    target_node = relationship("MapNode", foreign_keys=[to_node])

class TrafficFlow(Base):
    __tablename__ = "traffic_flows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    segment_id: Mapped[int] = mapped_column(ForeignKey("road_segments.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    speed_kmh: Mapped[float] = mapped_column(Float, nullable=False)
    density: Mapped[float] = mapped_column(Float, nullable=False)
    travel_time_sec: Mapped[float] = mapped_column(Float, nullable=False)

    segment = relationship("RoadSegment")

class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    location = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    affected_segments: Mapped[List[Any]] = mapped_column(JSON, nullable=False)
