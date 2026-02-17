from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.models.base import Base

class ReactorType(str, Enum):
    PWR = "PWR"
    BWR = "BWR"
    SMR = "SMR"

class ReactorStatus(str, Enum):
    OPERATING = "operating"
    SHUTDOWN = "shutdown"
    MAINTENANCE = "maintenance"

class SafetySystemType(str, Enum):
    SCRAM = "SCRAM"
    ECCS = "ECCS"
    CONTAINMENT = "containment"

class SafetySystemStatus(str, Enum):
    ACTIVE = "active"
    STANDBY = "standby"
    FAILED = "failed"

class SensorParameter(str, Enum):
    TEMPERATURE = "temp"
    PRESSURE = "pressure"
    NEUTRON_FLUX = "neutron_flux"
    COOLANT_FLOW = "coolant_flow"

class Reactor(Base):
    __tablename__ = "reactors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plant_id: Mapped[int] = mapped_column(Integer, index=True)
    reactor_type: Mapped[ReactorType] = mapped_column(String)
    thermal_power_mw: Mapped[float] = mapped_column(Float)
    status: Mapped[ReactorStatus] = mapped_column(String, default=ReactorStatus.OPERATING)
    core_temperature: Mapped[float] = mapped_column(Float)

    # Relationships
    sensor_readings: Mapped[List["SensorReading"]] = relationship("SensorReading", back_populates="reactor")
    safety_systems: Mapped[List["SafetySystem"]] = relationship("SafetySystem", back_populates="reactor")

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reactor_id: Mapped[int] = mapped_column(ForeignKey("reactors.id"))
    sensor_id: Mapped[str] = mapped_column(String)
    parameter: Mapped[SensorParameter] = mapped_column(String)
    value: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_alarm: Mapped[bool] = mapped_column(Boolean, default=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)

    reactor: Mapped["Reactor"] = relationship("Reactor", back_populates="sensor_readings")

class SafetySystem(Base):
    __tablename__ = "safety_systems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reactor_id: Mapped[int] = mapped_column(ForeignKey("reactors.id"))
    system_type: Mapped[SafetySystemType] = mapped_column(String)
    status: Mapped[SafetySystemStatus] = mapped_column(String)
    last_test: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    reactor: Mapped["Reactor"] = relationship("Reactor", back_populates="safety_systems")
