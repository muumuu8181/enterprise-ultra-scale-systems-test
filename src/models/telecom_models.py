from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from src.core.database import Base

class SimType(str, enum.Enum):
    physical = "physical"
    esim = "esim"

class CallType(str, enum.Enum):
    voice = "voice"
    video = "video"
    conference = "conference"

class SessionType(str, enum.Enum):
    four_g = "4G"
    five_g = "5G"
    wifi = "WiFi"

class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, index=True)
    msisdn = Column(String, unique=True, index=True)
    plan_id = Column(Integer, ForeignKey("data_plans.id"))
    status = Column(String)
    imsi = Column(String, unique=True)
    sim_type = Column(Enum(SimType))

    plan = relationship("DataPlan", back_populates="subscribers")
    data_usage = relationship("DataUsage", back_populates="subscriber")

class DataPlan(Base):
    __tablename__ = "data_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    data_gb = Column(Integer)
    validity_days = Column(Integer)
    price = Column(Float)
    throttle_speed_after_limit = Column(Float)

    subscribers = relationship("Subscriber", back_populates="plan")

class CallRecord(Base):
    __tablename__ = "call_records"

    id = Column(Integer, primary_key=True, index=True)
    caller_id = Column(Integer, ForeignKey("subscribers.id"))
    callee_id = Column(Integer, ForeignKey("subscribers.id"))
    duration_sec = Column(Integer)
    call_type = Column(Enum(CallType))
    cost = Column(Float)

class DataUsage(Base):
    __tablename__ = "data_usage"

    id = Column(Integer, primary_key=True, index=True)
    subscriber_id = Column(Integer, ForeignKey("subscribers.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    bytes_used = Column(Integer)
    session_type = Column(Enum(SessionType))

    subscriber = relationship("Subscriber", back_populates="data_usage")
