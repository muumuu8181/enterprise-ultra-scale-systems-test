from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import declarative_base, relationship
import enum
from datetime import datetime

Base = declarative_base()

class LogSourceType(enum.Enum):
    SYSLOG = "syslog"
    WINDOWS = "windows"
    CLOUD = "cloud"

class AlertStatus(enum.Enum):
    NEW = "new"
    INVESTIGATING = "investigating"
    CLOSED = "closed"

class LogSource(Base):
    __tablename__ = "log_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    source_type = Column(SAEnum(LogSourceType), nullable=False)
    ip_address = Column(String, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow)
    event_rate = Column(Float, default=0.0)

class SIEMRule(Base):
    __tablename__ = "siem_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    detection_logic = Column(String, nullable=False)
    mitre_tactic = Column(String, nullable=True)
    enabled = Column(Boolean, default=True)
    last_triggered = Column(DateTime, nullable=True)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("siem_rules.id"), nullable=True)
    severity = Column(String, nullable=False)
    status = Column(SAEnum(AlertStatus), default=AlertStatus.NEW)
    assigned_to = Column(String, nullable=True)
    false_positive = Column(Boolean, default=False)

    rule = relationship("SIEMRule")
