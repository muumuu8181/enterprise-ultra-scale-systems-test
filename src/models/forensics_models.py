import enum
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, Enum as SQLEnum, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class CaseType(str, enum.Enum):
    INCIDENT_RESPONSE = "incident_response"
    LITIGATION = "litigation"
    COMPLIANCE = "compliance"

class CaseStatus(str, enum.Enum):
    INTAKE = "intake"
    ACQUISITION = "acquisition"
    ANALYSIS = "analysis"
    REPORTING = "reporting"
    CLOSED = "closed"

class EvidenceType(str, enum.Enum):
    DISK_IMAGE = "disk_image"
    MEMORY_DUMP = "memory_dump"
    NETWORK_CAPTURE = "network_capture"
    MOBILE = "mobile"

class FindingType(str, enum.Enum):
    MALWARE = "malware"
    DATA_EXFIL = "data_exfil"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DELETED_FILES = "deleted_files"

class ForensicCase(Base):
    __tablename__ = "forensic_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    case_type: Mapped[CaseType] = mapped_column(SQLEnum(CaseType))
    subject: Mapped[str] = mapped_column(String)
    status: Mapped[CaseStatus] = mapped_column(SQLEnum(CaseStatus), default=CaseStatus.INTAKE)
    lead_examiner_id: Mapped[str] = mapped_column(String)
    priority: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evidence_items: Mapped[List["EvidenceItem"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    findings: Mapped[List["Finding"]] = relationship(back_populates="case", cascade="all, delete-orphan")

class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("forensic_cases.id"))
    item_type: Mapped[EvidenceType] = mapped_column(SQLEnum(EvidenceType))
    hash_md5: Mapped[Optional[str]] = mapped_column(String)
    hash_sha256: Mapped[Optional[str]] = mapped_column(String)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    chain_of_custody: Mapped[Any] = mapped_column(JSON, default=list)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    case: Mapped["ForensicCase"] = relationship(back_populates="evidence_items")
    findings: Mapped[List["Finding"]] = relationship(back_populates="evidence", cascade="all, delete-orphan")

class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("forensic_cases.id"))
    evidence_id: Mapped[int] = mapped_column(ForeignKey("evidence_items.id"))
    finding_type: Mapped[FindingType] = mapped_column(SQLEnum(FindingType))
    severity: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    artifacts: Mapped[Any] = mapped_column(JSON, default=list)
    timestamp_range: Mapped[Optional[str]] = mapped_column(String)

    case: Mapped["ForensicCase"] = relationship(back_populates="findings")
    evidence: Mapped["EvidenceItem"] = relationship(back_populates="findings")
