from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
import enum
from datetime import datetime

class DebrisObjectType(enum.Enum):
    rocket_body = "rocket_body"
    payload = "payload"
    fragment = "fragment"

class ConjunctionStatus(enum.Enum):
    monitoring = "monitoring"
    warning = "warning"
    alert = "alert"
    maneuver_planned = "maneuver_planned"

class ManeuverStatus(enum.Enum):
    planned = "planned"
    approved = "approved"
    executed = "executed"

class DebrisObject(Base):
    __tablename__ = "debris_objects"

    id = Column(Integer, primary_key=True, index=True)
    norad_id = Column(Integer, unique=True, index=True)
    object_type = Column(Enum(DebrisObjectType))
    size_cm = Column(Float)
    mass_kg = Column(Float)
    orbit_altitude_km = Column(Float)
    inclination_deg = Column(Float)
    tle_line1 = Column(String)
    tle_line2 = Column(String)
    last_observed = Column(DateTime, default=datetime.utcnow)

class ConjunctionEvent(Base):
    __tablename__ = "conjunction_events"

    id = Column(Integer, primary_key=True, index=True)
    primary_object_id = Column(Integer, ForeignKey("debris_objects.id"))
    secondary_object_id = Column(Integer, ForeignKey("debris_objects.id"))
    tca = Column(DateTime)
    miss_distance_m = Column(Float)
    collision_probability = Column(Float)
    status = Column(Enum(ConjunctionStatus))

    primary_object = relationship("DebrisObject", foreign_keys=[primary_object_id])
    secondary_object = relationship("DebrisObject", foreign_keys=[secondary_object_id])

class ManeuverPlan(Base):
    __tablename__ = "maneuver_plans"

    id = Column(Integer, primary_key=True, index=True)
    conjunction_id = Column(Integer, ForeignKey("conjunction_events.id"))
    satellite_id = Column(Integer, ForeignKey("debris_objects.id"))
    delta_v = Column(Float)
    burn_duration_sec = Column(Float)
    execution_time = Column(DateTime)
    fuel_cost_kg = Column(Float)
    status = Column(Enum(ManeuverStatus))

    conjunction = relationship("ConjunctionEvent")
    satellite = relationship("DebrisObject")
