from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import JSON
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import Optional, List, Dict, Any

class Sensor(Base):
    """
    IoTセンサーモデル
    """
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    sensor_type: Mapped[str] = mapped_column(String)
    # PostGISのPOINT型 (SRID 4326: WGS84)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    status: Mapped[str] = mapped_column(String, default="active")
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # メタデータはJSON形式で保存
    metadata_info: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, nullable=True)

    readings: Mapped[List["SensorReading"]] = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="sensor", cascade="all, delete-orphan")

class SensorReading(Base):
    """
    センサー読み取り値モデル
    """
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sensor_id: Mapped[int] = mapped_column(Integer, ForeignKey("sensors.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String)
    quality_score: Mapped[float] = mapped_column(Float)

    sensor: Mapped["Sensor"] = relationship("Sensor", back_populates="readings")

class Alert(Base):
    """
    アラートモデル
    """
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sensor_id: Mapped[int] = mapped_column(Integer, ForeignKey("sensors.id"))
    alert_type: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    sensor: Mapped["Sensor"] = relationship("Sensor", back_populates="alerts")

class TrafficSignal(Base):
    """
    信号機モデル
    """
    __tablename__ = "traffic_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    intersection_id: Mapped[str] = mapped_column(String, index=True)
    signal_group: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String) # RED, YELLOW, GREEN
    cycle_time: Mapped[int] = mapped_column(Integer)
    green_time: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmergencyIncident(Base):
    """
    緊急インシデントモデル
    """
    __tablename__ = "emergency_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_type: Mapped[str] = mapped_column(String)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    status: Mapped[str] = mapped_column(String) # REPORTED, DISPATCHED, CLEARED
    priority: Mapped[int] = mapped_column(Integer)
    units_dispatched: Mapped[List[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
