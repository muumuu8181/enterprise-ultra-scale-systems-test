from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base
from geoalchemy2 import Geometry
import enum
from datetime import datetime

# Import Base from src.database
# If src.database is not importable due to path issues in this env, we might need a workaround,
# but assuming standard python path or running as module, it should work.
try:
    from src.database import Base
except ImportError:
    # Fallback for when running in isolation or without src in path
    Base = declarative_base()

class TriageLevel(str, enum.Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"

class CallStatus(str, enum.Enum):
    RECEIVED = "received"
    DISPATCHED = "dispatched"
    ON_SCENE = "on_scene"
    TRANSPORTING = "transporting"
    COMPLETED = "completed"

class UnitType(str, enum.Enum):
    ALS = "als"
    BLS = "bls"
    CRITICAL_CARE = "critical_care"

class UnitStatus(str, enum.Enum):
    AVAILABLE = "available"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    AT_HOSPITAL = "at_hospital"

class AmbulanceUnit(Base):
    __tablename__ = "ambulance_units"

    id = Column(Integer, primary_key=True, index=True)
    call_sign = Column(String, unique=True, index=True)
    unit_type = Column(Enum(UnitType))
    crew = Column(JSON)
    location = Column(Geometry('POINT'))
    base_station_id = Column(Integer)
    status = Column(Enum(UnitStatus), default=UnitStatus.AVAILABLE)

    # Relationship to calls assigned to this unit
    calls = relationship("EmergencyCall", back_populates="assigned_unit")


class EmergencyCall(Base):
    __tablename__ = "emergency_calls"

    id = Column(Integer, primary_key=True, index=True)
    caller_phone = Column(String)
    location = Column(Geometry('POINT'))
    complaint = Column(String)
    triage_level = Column(Enum(TriageLevel))
    dispatcher_id = Column(Integer)
    assigned_unit_id = Column(Integer, ForeignKey("ambulance_units.id"), nullable=True)
    call_time = Column(DateTime, default=datetime.utcnow)
    dispatch_time = Column(DateTime, nullable=True)
    status = Column(Enum(CallStatus), default=CallStatus.RECEIVED)

    assigned_unit = relationship("AmbulanceUnit", back_populates="calls")
    patient_record = relationship("PatientRecord", back_populates="call", uselist=False)


class PatientRecord(Base):
    __tablename__ = "patient_records"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("emergency_calls.id"))
    age = Column(Integer)
    gender = Column(String)
    chief_complaint = Column(String)
    vitals = Column(JSON)
    interventions = Column(JSON)
    destination_hospital = Column(String)
    handoff_time = Column(DateTime, nullable=True)
    outcome = Column(String, nullable=True)

    call = relationship("EmergencyCall", back_populates="patient_record")
