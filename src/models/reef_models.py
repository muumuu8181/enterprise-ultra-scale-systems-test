from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base
from geoalchemy2 import Geometry
import enum
from datetime import datetime

Base = declarative_base()

class ReefType(str, enum.Enum):
    fringing = "fringing"
    barrier = "barrier"
    atoll = "atoll"

class AlertLevel(str, enum.Enum):
    watch = "watch"
    warning = "warning"
    alert1 = "alert1"
    alert2 = "alert2"

class AlertStatus(str, enum.Enum):
    active = "active"
    resolved = "resolved"

class ReefSite(Base):
    __tablename__ = "reef_sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # Storing as Geometry, will be serialized as GeoJSON in API
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    country = Column(String, nullable=False)
    reef_type = Column(Enum(ReefType), nullable=False)
    area_sq_km = Column(Float, nullable=True)
    protection_status = Column(String, nullable=True)
    last_survey_date = Column(DateTime, nullable=True)

    surveys = relationship("SurveyRecord", back_populates="site")
    alerts = relationship("BleachingAlert", back_populates="site")

class SurveyRecord(Base):
    __tablename__ = "survey_records"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("reef_sites.id"), nullable=False)
    surveyor_id = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    coral_cover_pct = Column(Float, nullable=False)
    bleaching_pct = Column(Float, nullable=False)
    species_count = Column(Integer, nullable=False)
    water_temp_c = Column(Float, nullable=False)
    ph_level = Column(Float, nullable=False)
    visibility_m = Column(Float, nullable=False)
    photos = Column(JSON, nullable=True)

    site = relationship("ReefSite", back_populates="surveys")

class BleachingAlert(Base):
    __tablename__ = "bleaching_alerts"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("reef_sites.id"), nullable=False)
    alert_level = Column(Enum(AlertLevel), nullable=False)
    degree_heating_weeks = Column(Float, nullable=False)
    satellite_sst_c = Column(Float, nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(AlertStatus), default=AlertStatus.active)

    site = relationship("ReefSite", back_populates="alerts")
