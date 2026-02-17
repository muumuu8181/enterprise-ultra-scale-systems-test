from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import List, Optional, Any

class SmartMeter(Base):
    """
    Smart Meter Model
    """
    __tablename__ = "smart_meters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meter_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    district: Mapped[str] = mapped_column(String, index=True)
    customer_type: Mapped[str] = mapped_column(String)
    installed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    readings: Mapped[List["EnergyReading"]] = relationship("EnergyReading", back_populates="meter", cascade="all, delete-orphan")

class EnergyReading(Base):
    """
    Energy Reading Model
    """
    __tablename__ = "energy_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("smart_meters.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    kwh: Mapped[float] = mapped_column(Float)
    voltage: Mapped[float] = mapped_column(Float)
    current: Mapped[float] = mapped_column(Float)
    power_factor: Mapped[float] = mapped_column(Float)

    meter: Mapped["SmartMeter"] = relationship("SmartMeter", back_populates="readings")

class DemandResponse(Base):
    """
    Demand Response Event Model
    """
    __tablename__ = "demand_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    target_reduction: Mapped[float] = mapped_column(Float)
    actual_reduction: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
