from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class PipelineType(str, PyEnum):
    CRUDE = "crude"
    GAS = "gas"
    REFINED = "refined"

class SensorType(str, PyEnum):
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    FLOW = "flow"
    VIBRATION = "vibration"
    ACOUSTIC = "acoustic"

class IncidentType(str, PyEnum):
    LEAK = "leak"
    RUPTURE = "rupture"
    CORROSION = "corrosion"
    PIG_STUCK = "pig_stuck"

class Severity(str, PyEnum):
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"

class ResponseStatus(str, PyEnum):
    DETECTED = "detected"
    RESPONDING = "responding"
    CONTAINED = "contained"
    RESOLVED = "resolved"

class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    pipeline_type: Mapped[PipelineType] = mapped_column(Enum(PipelineType))
    length_km: Mapped[float] = mapped_column(Float)
    diameter_inches: Mapped[float] = mapped_column(Float)
    max_pressure_psi: Mapped[float] = mapped_column(Float)
    start_location: Mapped[str] = mapped_column(String(255))
    end_location: Mapped[str] = mapped_column(String(255))
    commissioned_date: Mapped[datetime] = mapped_column(DateTime)

    readings: Mapped[List["SensorReading"]] = relationship(back_populates="pipeline")
    incidents: Mapped[List["Incident"]] = relationship(back_populates="pipeline")

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    pipeline_id: Mapped[int] = mapped_column(ForeignKey("pipelines.id"))
    sensor_type: Mapped[SensorType] = mapped_column(Enum(SensorType))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))
    location_km: Mapped[float] = mapped_column(Float)
    reading_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    anomaly_detected: Mapped[bool] = mapped_column(Boolean, default=False)

    pipeline: Mapped["Pipeline"] = relationship(back_populates="readings")

class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    pipeline_id: Mapped[int] = mapped_column(ForeignKey("pipelines.id"))
    incident_type: Mapped[IncidentType] = mapped_column(Enum(IncidentType))
    severity: Mapped[Severity] = mapped_column(Enum(Severity))
    location_km: Mapped[float] = mapped_column(Float)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    response_status: Mapped[ResponseStatus] = mapped_column(Enum(ResponseStatus), default=ResponseStatus.DETECTED)

    pipeline: Mapped["Pipeline"] = relationship(back_populates="incidents")
