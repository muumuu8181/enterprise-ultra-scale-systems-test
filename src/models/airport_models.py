from __future__ import annotations
from typing import List, Optional
from datetime import datetime, date
import enum
from sqlalchemy import String, Integer, DateTime, Date, ForeignKey, Float, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel

class Base(DeclarativeBase):
    pass

class FlightStatus(enum.Enum):
    ON_TIME = "on_time"
    DELAYED = "delayed"
    CANCELLED = "cancelled"

class GateStatus(enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    BOARDING = "boarding"

class BaggageStatus(enum.Enum):
    CHECKED_IN = "checked_in"
    LOADED = "loaded"
    IN_CAROUSEL = "in_carousel"
    CLAIMED = "claimed"

class Flight(Base):
    __tablename__ = "flights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flight_number: Mapped[str] = mapped_column(String)
    airline: Mapped[str] = mapped_column(String)
    origin: Mapped[str] = mapped_column(String)
    destination: Mapped[str] = mapped_column(String)
    scheduled_dep: Mapped[datetime] = mapped_column(DateTime)
    actual_dep: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[FlightStatus] = mapped_column(SAEnum(FlightStatus))
    gate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("gates.id"), nullable=True)
    aircraft_type: Mapped[str] = mapped_column(String)

    # Relationships
    gate: Mapped[Optional["Gate"]] = relationship("Gate", back_populates="current_flight", foreign_keys=[gate_id])
    baggage: Mapped[List["Baggage"]] = relationship("Baggage", back_populates="flight")

class Gate(Base):
    __tablename__ = "gates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    terminal: Mapped[str] = mapped_column(String)
    gate_number: Mapped[str] = mapped_column(String)
    status: Mapped[GateStatus] = mapped_column(SAEnum(GateStatus))
    assigned_flight_id: Mapped[Optional[int]] = mapped_column(ForeignKey("flights.id"), nullable=True)
    next_available: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    # Note: assigned_flight_id might be redundant if we have a relationship via Flight.gate_id
    # But the prompt explicitly requested `assigned_flight_id`.
    # Let's keep it consistent. A gate can be assigned to a flight.
    current_flight: Mapped[Optional["Flight"]] = relationship("Flight", back_populates="gate", foreign_keys="Flight.gate_id")

class Baggage(Base):
    __tablename__ = "baggage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flight_id: Mapped[int] = mapped_column(ForeignKey("flights.id"))
    passenger_id: Mapped[str] = mapped_column(String)
    tag_number: Mapped[str] = mapped_column(String)
    status: Mapped[BaggageStatus] = mapped_column(SAEnum(BaggageStatus))
    weight_kg: Mapped[float] = mapped_column(Float)

    # Relationships
    flight: Mapped["Flight"] = relationship("Flight", back_populates="baggage")

class GateAssignment(BaseModel):
    gate_id: int
    flight_id: int
    assigned_time: datetime
