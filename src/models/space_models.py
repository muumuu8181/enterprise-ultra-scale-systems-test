from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import List, Any

class Satellite(Base):
    """
    衛星モデル
    """
    __tablename__ = "satellites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    orbit_type: Mapped[str] = mapped_column(String) # LEO/MEO/GEO
    inclination: Mapped[float] = mapped_column(Float)
    altitude_km: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String)

    telemetry: Mapped[List["Telemetry"]] = relationship("Telemetry", back_populates="satellite", cascade="all, delete-orphan")
    commands: Mapped[List["MissionCommand"]] = relationship("MissionCommand", back_populates="satellite", cascade="all, delete-orphan")

class Telemetry(Base):
    """
    テレメトリデータモデル
    """
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    satellite_id: Mapped[int] = mapped_column(Integer, ForeignKey("satellites.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    position: Mapped[dict] = mapped_column(JSON) # JSON: {x: ..., y: ..., z: ...}
    velocity: Mapped[dict] = mapped_column(JSON) # JSON: {vx: ..., vy: ..., vz: ...}
    battery_percent: Mapped[float] = mapped_column(Float)
    temperature_c: Mapped[float] = mapped_column(Float)
    anomalies: Mapped[dict] = mapped_column(JSON) # JSON array or object

    satellite: Mapped["Satellite"] = relationship("Satellite", back_populates="telemetry")

class GroundStation(Base):
    """
    地上局モデル
    """
    __tablename__ = "ground_stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    # PostGISのPOINT型 (SRID 4326: WGS84)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    antenna_count: Mapped[int] = mapped_column(Integer)
    frequency_bands: Mapped[dict] = mapped_column(JSON) # JSON array: ["S-band", "X-band"]

class MissionCommand(Base):
    """
    ミッションコマンドモデル
    """
    __tablename__ = "mission_commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    satellite_id: Mapped[int] = mapped_column(Integer, ForeignKey("satellites.id"))
    command_type: Mapped[str] = mapped_column(String)
    parameters: Mapped[dict] = mapped_column(JSON)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    result: Mapped[str] = mapped_column(String, nullable=True)

    satellite: Mapped["Satellite"] = relationship("Satellite", back_populates="commands")
