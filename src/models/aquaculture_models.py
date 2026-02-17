from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum as SqlEnum, JSON
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2 import Geometry
import enum
from datetime import datetime, timezone

Base = declarative_base()

class FarmType(str, enum.Enum):
    CAGE = "cage"
    POND = "pond"
    RAS = "ras"
    OFFSHORE = "offshore"

class FishFarm(Base):
    __tablename__ = "fish_farms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # location: GeoJSON. Storing as Geometry in PostGIS.
    location = Column(Geometry(geometry_type='GEOMETRY', srid=4326))
    farm_type = Column(SqlEnum(FarmType), nullable=False)
    species = Column(JSON, nullable=False)
    capacity_tonnes = Column(Float)
    license_number = Column(String, unique=True)
    operator_id = Column(String)

class WaterQuality(Base):
    __tablename__ = "water_quality_measurements"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("fish_farms.id"), nullable=False)
    sensor_id = Column(String, nullable=False)
    temperature_c = Column(Float)
    dissolved_oxygen_ppm = Column(Float)
    ph = Column(Float)
    ammonia_ppm = Column(Float)
    salinity_ppt = Column(Float)
    turbidity = Column(Float)
    measured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    alert_triggered = Column(Boolean, default=False)

class FeedingSchedule(Base):
    __tablename__ = "feeding_schedules"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("fish_farms.id"), nullable=False)
    feed_type = Column(String, nullable=False)
    quantity_kg = Column(Float, nullable=False)
    feeding_time = Column(DateTime, nullable=False)
    fcr_target = Column(Float)
    actual_fcr = Column(Float)
    biomass_estimate_kg = Column(Float)
    mortality_count = Column(Integer, default=0)
    logged_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
