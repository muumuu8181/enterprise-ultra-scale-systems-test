from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.db.base import Base
import enum
from datetime import datetime

class SeverityLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class IOCType(str, enum.Enum):
    IP = "ip"
    DOMAIN = "domain"
    HASH = "hash"
    URL = "url"

class TLPMarking(str, enum.Enum):
    RED = "RED"
    AMBER = "AMBER"
    GREEN = "GREEN"
    WHITE = "WHITE"

class VulnStatus(str, enum.Enum):
    OPEN = "open"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"

class ThreatIndicator(Base):
    __tablename__ = "threat_indicators"

    id = Column(Integer, primary_key=True, index=True)
    ioc_type = Column(Enum(IOCType), nullable=False)
    value = Column(String, nullable=False, index=True)
    severity = Column(Enum(SeverityLevel), nullable=False)
    confidence = Column(Float, nullable=False)
    tlp_marking = Column(Enum(TLPMarking), nullable=True)

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True) # Minimal field

class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    source_ip = Column(String, nullable=True)
    dest_ip = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    raw_log = Column(Text, nullable=True)
    mitre_technique_id = Column(String, nullable=True)

    # Optional: Relationship to campaign if we wanted to persist correlation
    # campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    cve_id = Column(String, nullable=False, unique=True)
    cvss_score = Column(Float, nullable=False)
    affected_system = Column(String, nullable=False)
    status = Column(Enum(VulnStatus), default=VulnStatus.OPEN)
    sla_deadline = Column(DateTime, nullable=True)
