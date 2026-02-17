from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import JSON
from src.database import Base
from datetime import datetime
from typing import Optional, List, Dict, Any

class DigitalTwin(Base):
    __tablename__ = "digital_twins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    physical_asset_id: Mapped[str] = mapped_column(String, index=True)
    asset_type: Mapped[str] = mapped_column(String) # building/factory/city/vehicle
    model_uri: Mapped[str] = mapped_column(String)
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sync_interval_sec: Mapped[int] = mapped_column(Integer, default=60)

    states: Mapped[List["TwinState"]] = relationship("TwinState", back_populates="twin", cascade="all, delete-orphan")
    simulations: Mapped[List["TwinSimulation"]] = relationship("TwinSimulation", back_populates="twin", cascade="all, delete-orphan")

class TwinState(Base):
    __tablename__ = "twin_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    twin_id: Mapped[int] = mapped_column(Integer, ForeignKey("digital_twins.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    state_data: Mapped[Dict[str, Any]] = mapped_column(JSON)
    simulation_mode: Mapped[str] = mapped_column(String, default="real") # real/predicted

    twin: Mapped["DigitalTwin"] = relationship("DigitalTwin", back_populates="states")

class TwinSimulation(Base):
    __tablename__ = "twin_simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    twin_id: Mapped[int] = mapped_column(Integer, ForeignKey("digital_twins.id"))
    scenario_name: Mapped[str] = mapped_column(String)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="queued") # queued/running/completed/failed
    result_uri: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    twin: Mapped["DigitalTwin"] = relationship("DigitalTwin", back_populates="simulations")
