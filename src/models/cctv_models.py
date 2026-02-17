from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import JSON
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import Optional, List, Dict, Any

class CCTVCamera(Base):
    """
    CCTVカメラモデル
    """
    __tablename__ = "cctv_cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    camera_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    coverage_area: Mapped[Any] = mapped_column(Geometry("POLYGON", srid=4326), nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")
    stream_url: Mapped[str] = mapped_column(String, nullable=True)
    enabled_analytics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    analytics: Mapped[List["CCTVAnalytics"]] = relationship("CCTVAnalytics", back_populates="camera", cascade="all, delete-orphan")
    incidents: Mapped[List["CCTVIncident"]] = relationship("CCTVIncident", back_populates="camera", cascade="all, delete-orphan")

class CCTVAnalytics(Base):
    """
    CCTV解析結果モデル
    """
    __tablename__ = "cctv_analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    camera_id: Mapped[int] = mapped_column(Integer, ForeignKey("cctv_cameras.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    crowd_density: Mapped[float] = mapped_column(Float)
    vehicle_count: Mapped[int] = mapped_column(Integer)
    anomaly_detected: Mapped[bool] = mapped_column(Boolean, default=False)

    camera: Mapped["CCTVCamera"] = relationship("CCTVCamera", back_populates="analytics")

class CCTVIncident(Base):
    """
    CCTVインシデント記録モデル
    """
    __tablename__ = "cctv_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    camera_id: Mapped[int] = mapped_column(Integer, ForeignKey("cctv_cameras.id"))
    incident_type: Mapped[str] = mapped_column(String)
    screenshot_url: Mapped[str] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    camera: Mapped["CCTVCamera"] = relationship("CCTVCamera", back_populates="incidents")
