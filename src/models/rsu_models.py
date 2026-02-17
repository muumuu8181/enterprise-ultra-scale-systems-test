from datetime import datetime
from typing import List, Optional
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    pass

class RSUnit(Base):
    __tablename__ = "rsu_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rsu_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    location: Mapped[str] = mapped_column(Geometry("POINT", srid=4326))
    coverage_radius: Mapped[float] = mapped_column(Float)
    broadcast_interval_ms: Mapped[int] = mapped_column(Integer, default=100)
    power_level_dbm: Mapped[float] = mapped_column(Float, default=20.0)
    status: Mapped[str] = mapped_column(String, default="offline")
    firmware_version: Mapped[str] = mapped_column(String)
    last_heartbeat: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship to coverage
    coverages: Mapped[List["RSUCoverage"]] = relationship(back_populates="rsu", cascade="all, delete-orphan")

class RSUCoverage(Base):
    __tablename__ = "rsu_coverages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rsu_id: Mapped[int] = mapped_column(ForeignKey("rsu_units.id"), index=True)
    covered_area: Mapped[str] = mapped_column(Geometry("POLYGON", srid=4326))
    vehicle_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    rsu: Mapped["RSUnit"] = relationship(back_populates="coverages")
