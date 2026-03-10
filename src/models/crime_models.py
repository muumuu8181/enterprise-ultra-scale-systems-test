from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class ActivityType(str, PyEnum):
    STRUCTURING = "structuring"
    LAYERING = "layering"
    SMURFING = "smurfing"

class CaseStatus(str, PyEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    ESCALATED = "escalated"
    CLOSED = "closed"

class CasePriority(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EntityType(str, PyEnum):
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"

class SuspiciousActivity(Base):
    __tablename__ = "suspicious_activities"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String, index=True, nullable=False)
    activity_type = Column(Enum(ActivityType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False)
    flagged_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    investigator_id = Column(String, nullable=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.OPEN, nullable=False)

class InvestigationCase(Base):
    __tablename__ = "investigation_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String, unique=True, index=True, nullable=False)
    activities = Column(JSON, nullable=False)
    assigned_to = Column(String, nullable=True)
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM, nullable=False)
    findings = Column(String, nullable=True)
    sar_filed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String, unique=True, index=True, nullable=False)
    entity_type = Column(Enum(EntityType), nullable=False)
    risk_level = Column(Float, nullable=False)
    pep_status = Column(Boolean, default=False, nullable=False)
    sanctions_match = Column(Boolean, default=False, nullable=False)
    adverse_media = Column(Boolean, default=False, nullable=False)
    last_screened = Column(DateTime, default=datetime.utcnow, nullable=False)
