from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import JSON
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import Optional, List, Dict, Any

class AQStation(Base):
    """
    大気質観測局モデル
    """
    __tablename__ = "aq_stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    station_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    # PostGIS POINT (SRID 4326)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    operator: Mapped[str] = mapped_column(String)
    installed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    readings: Mapped[List["AQReading"]] = relationship("AQReading", back_populates="station", cascade="all, delete-orphan")
    alerts: Mapped[List["AQAlert"]] = relationship("AQAlert", back_populates="station", cascade="all, delete-orphan")

class AQReading(Base):
    """
    大気質測定データモデル
    """
    __tablename__ = "aq_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    station_id: Mapped[int] = mapped_column(Integer, ForeignKey("aq_stations.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Pollutants (µg/m3 or ppm depending on standard, usually stored as float)
    pm25: Mapped[float] = mapped_column(Float, nullable=True)
    pm10: Mapped[float] = mapped_column(Float, nullable=True)
    no2: Mapped[float] = mapped_column(Float, nullable=True)
    o3: Mapped[float] = mapped_column(Float, nullable=True)
    co: Mapped[float] = mapped_column(Float, nullable=True)

    aqi: Mapped[int] = mapped_column(Integer, nullable=True)

    station: Mapped["AQStation"] = relationship("AQStation", back_populates="readings")

class AQAlert(Base):
    """
    大気質アラート履歴モデル
    """
    __tablename__ = "aq_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    station_id: Mapped[int] = mapped_column(Integer, ForeignKey("aq_stations.id"))
    aqi_value: Mapped[int] = mapped_column(Integer)
    level: Mapped[str] = mapped_column(String) # good, moderate, unhealthy, hazardous
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    station: Mapped["AQStation"] = relationship("AQStation", back_populates="alerts")

class AQAlertRule(Base):
    """
    アラート設定ルールモデル
    """
    __tablename__ = "aq_alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    threshold_aqi: Mapped[int] = mapped_column(Integer)
    # PostGIS POLYGON (SRID 4326)
    area_polygon: Mapped[Any] = mapped_column(Geometry("POLYGON", srid=4326))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
