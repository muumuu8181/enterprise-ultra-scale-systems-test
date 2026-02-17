from sqlalchemy import Column, Integer, String, Float, Enum as SQLEnum, Date, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import enum
from src.database import Base

class VesselType(str, enum.Enum):
    trawler = "trawler"
    longliner = "longliner"
    seiner = "seiner"
    gillnetter = "gillnetter"

class QuotaStatus(str, enum.Enum):
    active = "active"
    exhausted = "exhausted"
    suspended = "suspended"

class FishingVessel(Base):
    __tablename__ = "fishing_vessels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    registration_number = Column(String, unique=True, nullable=False)
    owner_id = Column(Integer, nullable=False)
    vessel_type = Column(SQLEnum(VesselType), nullable=False)
    length_m = Column(Float, nullable=False)
    port_base = Column(String, nullable=False)
    license_expiry = Column(Date, nullable=False)
    ais_mmsi = Column(String, unique=True, nullable=False)

    quotas = relationship("QuotaAllocation", back_populates="vessel")
    catch_reports = relationship("CatchReport", back_populates="vessel")

class QuotaAllocation(Base):
    __tablename__ = "quota_allocations"

    id = Column(Integer, primary_key=True, index=True)
    vessel_id = Column(Integer, ForeignKey("fishing_vessels.id"), nullable=False)
    species = Column(String, nullable=False)
    fishing_zone = Column(String, nullable=False)
    quota_tonnes = Column(Float, nullable=False)
    caught_tonnes = Column(Float, default=0.0)
    remaining_tonnes = Column(Float, nullable=False)
    season_start = Column(Date, nullable=False)
    season_end = Column(Date, nullable=False)
    status = Column(SQLEnum(QuotaStatus), default=QuotaStatus.active)

    vessel = relationship("FishingVessel", back_populates="quotas")

class CatchReport(Base):
    __tablename__ = "catch_reports"

    id = Column(Integer, primary_key=True, index=True)
    vessel_id = Column(Integer, ForeignKey("fishing_vessels.id"), nullable=False)
    species = Column(String, nullable=False)
    weight_kg = Column(Float, nullable=False)
    # Using Geometry('POINT', srid=4326) for lat/lon
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    catch_date = Column(DateTime, nullable=False)
    gear_type = Column(String, nullable=False)
    bycatch = Column(JSON, default={})
    verified = Column(Boolean, default=False)
    landing_port = Column(String, nullable=True)

    vessel = relationship("FishingVessel", back_populates="catch_reports")
