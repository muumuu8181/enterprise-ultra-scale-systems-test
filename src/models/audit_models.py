from enum import Enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.db.base import Base

class Chain(str, Enum):
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    BSC = "bsc"

class AuditStatus(str, Enum):
    PENDING = "pending"
    SCANNING = "scanning"
    COMPLETED = "completed"
    FAILED = "failed"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class VulnType(str, Enum):
    REENTRANCY = "reentrancy"
    OVERFLOW = "overflow"
    ACCESS_CONTROL = "access_control"
    FRONT_RUNNING = "front_running"
    OTHER = "other"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SmartContract(Base):
    __tablename__ = "smart_contracts"

    id = Column(Integer, primary_key=True, index=True)
    chain = Column(SAEnum(Chain), nullable=False)
    address = Column(String, nullable=True)
    abi = Column(JSON, nullable=True)
    source_code = Column(Text, nullable=False)
    compiler_version = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    audit_reports = relationship("AuditReport", back_populates="contract", cascade="all, delete-orphan")

class AuditReport(Base):
    __tablename__ = "audit_reports"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("smart_contracts.id"), nullable=False)
    status = Column(SAEnum(AuditStatus), default=AuditStatus.PENDING)
    vulnerabilities_found = Column(Integer, default=0)
    risk_level = Column(SAEnum(RiskLevel), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    contract = relationship("SmartContract", back_populates="audit_reports")
    vulnerabilities = relationship("Vulnerability", back_populates="audit_report", cascade="all, delete-orphan")

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(Integer, ForeignKey("audit_reports.id"), nullable=False)
    vuln_type = Column(SAEnum(VulnType), nullable=False)
    severity = Column(SAEnum(Severity), nullable=False)
    line_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    is_false_positive = Column(Boolean, default=False)

    audit_report = relationship("AuditReport", back_populates="vulnerabilities")
