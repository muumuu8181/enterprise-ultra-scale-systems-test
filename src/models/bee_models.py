from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from geoalchemy2 import Geometry
import enum
from datetime import datetime
from src.database import Base

class ColonyStrength(str, enum.Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"

class HiveStatus(str, enum.Enum):
    ACTIVE = "active"
    QUEENLESS = "queenless"
    SWARMING = "swarming"
    DEAD = "dead"

class BroodPattern(str, enum.Enum):
    SOLID = "solid"
    SPOTTY = "spotty"
    ABSENT = "absent"

class Apiary(Base):
    __tablename__ = "apiaries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    # Using Geometry type which is standard for PostGIS.
    # We will handle GeoJSON serialization/deserialization in the API layer or using geoalchemy2 functions.
    location = mapped_column(Geometry('POINT', srid=4326))
    owner_id: Mapped[int] = mapped_column(Integer)
    hive_count: Mapped[int] = mapped_column(Integer, default=0)
    primary_forage: Mapped[str] = mapped_column(String, nullable=True)
    altitude_m: Mapped[float] = mapped_column(Float, nullable=True)
    climate_zone: Mapped[str] = mapped_column(String, nullable=True)
    registered_since: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    hives = relationship("Hive", back_populates="apiary")

class Hive(Base):
    __tablename__ = "hives"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    apiary_id: Mapped[int] = mapped_column(ForeignKey("apiaries.id"))
    hive_number: Mapped[str] = mapped_column(String)
    queen_age_months: Mapped[int] = mapped_column(Integer, nullable=True)
    colony_strength: Mapped[ColonyStrength] = mapped_column(Enum(ColonyStrength), nullable=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float] = mapped_column(Float, nullable=True)
    sound_level_db: Mapped[float] = mapped_column(Float, nullable=True)
    status: Mapped[HiveStatus] = mapped_column(Enum(HiveStatus), default=HiveStatus.ACTIVE)

    apiary = relationship("Apiary", back_populates="hives")
    inspections = relationship("Inspection", back_populates="hive")

class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hive_id: Mapped[int] = mapped_column(ForeignKey("hives.id"))
    inspector_id: Mapped[int] = mapped_column(Integer)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    brood_pattern: Mapped[BroodPattern] = mapped_column(Enum(BroodPattern), nullable=True)
    queen_seen: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_signs: Mapped[dict] = mapped_column(JSON, nullable=True)
    honey_supers: Mapped[int] = mapped_column(Integer, default=0)
    varroa_count: Mapped[int] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(String, nullable=True)
    action_taken: Mapped[str] = mapped_column(String, nullable=True)

    hive = relationship("Hive", back_populates="inspections")
