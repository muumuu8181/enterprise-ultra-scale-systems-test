from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import enum

class IncidentType(str, enum.Enum):
    FIRE = "fire"
    MEDICAL = "medical"
    POLICE = "police"
    DISASTER = "disaster"

class IncidentStatus(str, enum.Enum):
    NEW = "new"
    DISPATCHED = "dispatched"
    RESPONDING = "responding"
    RESOLVED = "resolved"

class UnitType(str, enum.Enum):
    AMBULANCE = "ambulance"
    FIRE_TRUCK = "fire_truck"
    POLICE = "police"

class UnitStatus(str, enum.Enum):
    AVAILABLE = "available"
    DISPATCHED = "dispatched"
    BUSY = "busy"

class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_type: Mapped[IncidentType] = mapped_column(Enum(IncidentType))
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    severity: Mapped[int] = mapped_column(Integer) # 1-5
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus), default=IncidentStatus.NEW)
    caller_info: Mapped[Dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    dispatches: Mapped[List["Dispatch"]] = relationship("Dispatch", back_populates="incident")

class EmergencyUnit(Base):
    __tablename__ = "emergency_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    unit_type: Mapped[UnitType] = mapped_column(Enum(UnitType))
    call_sign: Mapped[str] = mapped_column(String, unique=True)
    status: Mapped[UnitStatus] = mapped_column(Enum(UnitStatus), default=UnitStatus.AVAILABLE)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    crew: Mapped[Dict[str, Any]] = mapped_column(JSON)

    dispatches: Mapped[List["Dispatch"]] = relationship("Dispatch", back_populates="unit")

class Dispatch(Base):
    __tablename__ = "dispatches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(Integer, ForeignKey("incidents.id"))
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("emergency_units.id"))
    dispatched_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    arrived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    response_time_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="dispatches")
    unit: Mapped["EmergencyUnit"] = relationship("EmergencyUnit", back_populates="dispatches")
