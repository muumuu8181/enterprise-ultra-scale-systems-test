from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from geoalchemy2 import Geometry
import datetime
import enum
from src.database import Base

class VesselType(enum.Enum):
    CARGO = "cargo"
    TANKER = "tanker"
    PASSENGER = "passenger"
    FISHING = "fishing"
    OTHER = "other"

class Vessel(Base):
    __tablename__ = "vessels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    mmsi: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    vessel_name: Mapped[str] = mapped_column(String, index=True)
    vessel_type: Mapped[VesselType] = mapped_column(Enum(VesselType))
    flag_country: Mapped[str] = mapped_column(String)
    length_m: Mapped[float] = mapped_column(Float)
    gross_tonnage: Mapped[int] = mapped_column(Integer)
    owner_id: Mapped[int] = mapped_column(Integer)

    positions = relationship("AISPosition", back_populates="vessel", cascade="all, delete-orphan")

class AISPosition(Base):
    __tablename__ = "ais_positions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vessel_id: Mapped[int] = mapped_column(ForeignKey("vessels.id"), index=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    speed_knots: Mapped[float] = mapped_column(Float)
    course: Mapped[float] = mapped_column(Float)
    navigational_status: Mapped[str] = mapped_column(String)
    draught: Mapped[float] = mapped_column(Float)
    # Using Geometry for efficient spatial queries
    location = Column(Geometry("POINT", srid=4326))

    vessel = relationship("Vessel", back_populates="positions")

class Port(Base):
    __tablename__ = "ports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    country: Mapped[str] = mapped_column(String)
    location = Column(Geometry("POINT", srid=4326))
    max_draught_m: Mapped[float] = mapped_column(Float)
    berths: Mapped[int] = mapped_column(Integer)
    facilities: Mapped[dict] = mapped_column(JSON)
