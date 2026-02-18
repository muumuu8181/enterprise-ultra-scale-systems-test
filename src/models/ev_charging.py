import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.database import Base

class ConnectorType(str, enum.Enum):
    TYPE2 = "type2"
    CHADEMO = "chademo"
    CCS = "ccs"

class ChargerStatus(str, enum.Enum):
    AVAILABLE = "available"
    CHARGING = "charging"
    FAULTED = "faulted"

class DemandResponseEventType(str, enum.Enum):
    PEAK_SHAVING = "peak_shaving"
    VALLEY_FILLING = "valley_filling"

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class EVCharger(Base):
    __tablename__ = "ev_chargers"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, index=True, nullable=False)
    connector_type = Column(SAEnum(ConnectorType), nullable=False)
    max_kw = Column(Float, nullable=False)
    status = Column(SAEnum(ChargerStatus), default=ChargerStatus.AVAILABLE, nullable=False)
    smart_charging_enabled = Column(Boolean, default=True)

    # Relationships
    sessions = relationship("ChargingSession", back_populates="charger")


class ChargingSession(Base):
    __tablename__ = "charging_sessions"

    id = Column(Integer, primary_key=True, index=True)
    charger_id = Column(Integer, ForeignKey("ev_chargers.id"), nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    vehicle_id = Column(Integer, index=True, nullable=False)
    started_at = Column(DateTime, default=utc_now)
    ended_at = Column(DateTime, nullable=True)
    kwh_delivered = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    charging_profile = Column(JSON, nullable=True)

    charger = relationship("EVCharger", back_populates="sessions")


class DemandResponse(Base):
    __tablename__ = "demand_responses"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, index=True, nullable=False)
    event_type = Column(SAEnum(DemandResponseEventType), nullable=False)
    period = Column(String, nullable=False)  # e.g. "2023-10-27T14:00/18:00"
    target_reduction_kw = Column(Float, nullable=False)
    achieved_kw = Column(Float, default=0.0)
