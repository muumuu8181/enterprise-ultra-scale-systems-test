from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import mapped_column, Mapped
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import Optional, Any

class WaterPressureSensor(Base):
    """
    水圧センサーモデル
    """
    __tablename__ = "water_pressure_sensors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    zone_id: Mapped[str] = mapped_column(String, index=True)
    # PostGISのPOINT型 (SRID 4326: WGS84)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    pressure_bar: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class WaterLeak(Base):
    """
    漏水レポートモデル
    """
    __tablename__ = "water_leaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    severity: Mapped[str] = mapped_column(String)
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    repaired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estimated_loss_liters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

class WaterQualityReading(Base):
    """
    水質データモデル
    """
    __tablename__ = "water_quality_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    station_id: Mapped[str] = mapped_column(String, index=True)
    ph: Mapped[float] = mapped_column(Float)
    turbidity: Mapped[float] = mapped_column(Float)
    chlorine_residual: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
