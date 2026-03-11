from sqlalchemy import Integer, String, Boolean, DateTime, Float, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
from typing import List, Optional
from src.database import Base

class ContractType(str, enum.Enum):
    NDA = "nda"
    MSA = "msa"
    SOW = "sow"
    EMPLOYMENT = "employment"
    LEASE = "lease"

class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"

class ClauseType(str, enum.Enum):
    LIABILITY = "liability"
    INDEMNITY = "indemnity"
    TERMINATION = "termination"
    IP = "ip"
    CONFIDENTIALITY = "confidentiality"

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AmendmentStatus(str, enum.Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"

class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    contract_type: Mapped[ContractType] = mapped_column(SQLEnum(ContractType))
    parties: Mapped[dict] = mapped_column(JSON)
    effective_date: Mapped[datetime] = mapped_column(DateTime)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    value: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String, default="USD")
    status: Mapped[ContractStatus] = mapped_column(SQLEnum(ContractStatus), default=ContractStatus.DRAFT)

    clauses: Mapped[List["Clause"]] = relationship("Clause", back_populates="contract")
    amendments: Mapped[List["Amendment"]] = relationship("Amendment", back_populates="contract")

class Clause(Base):
    __tablename__ = "clauses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"))
    clause_type: Mapped[ClauseType] = mapped_column(SQLEnum(ClauseType))
    text: Mapped[str] = mapped_column(String)
    risk_level: Mapped[RiskLevel] = mapped_column(SQLEnum(RiskLevel))
    ai_summary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    negotiable: Mapped[bool] = mapped_column(Boolean, default=True)

    contract: Mapped["Contract"] = relationship("Contract", back_populates="clauses")

class Amendment(Base):
    __tablename__ = "amendments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"))
    amendment_number: Mapped[int] = mapped_column(Integer)
    changes: Mapped[dict] = mapped_column(JSON)
    proposed_by: Mapped[str] = mapped_column(String)
    approved_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    effective_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[AmendmentStatus] = mapped_column(SQLEnum(AmendmentStatus), default=AmendmentStatus.PROPOSED)

    contract: Mapped["Contract"] = relationship("Contract", back_populates="amendments")
