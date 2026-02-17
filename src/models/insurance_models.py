from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, Dict

from sqlalchemy import Integer, String, Float, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.base import Base

class ProductType(str, PyEnum):
    LIFE = "life"
    HEALTH = "health"
    AUTO = "auto"
    PROPERTY = "property"

class PolicyStatus(str, PyEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"

class ClaimStatus(str, PyEnum):
    SUBMITTED = "submitted"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"

class UnderwritingDecision(str, PyEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"

class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    holder_id: Mapped[int] = mapped_column(Integer, index=True)
    product_type: Mapped[ProductType] = mapped_column(Enum(ProductType))
    premium: Mapped[float] = mapped_column(Float)
    coverage_amount: Mapped[float] = mapped_column(Float)
    status: Mapped[PolicyStatus] = mapped_column(Enum(PolicyStatus), default=PolicyStatus.ACTIVE)
    expiry_date: Mapped[datetime] = mapped_column(DateTime)

    claims = relationship("Claim", back_populates="policy")
    underwriting = relationship("Underwriting", back_populates="policy", uselist=False)

class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_id: Mapped[int] = mapped_column(Integer, ForeignKey("policies.id"))
    incident_date: Mapped[datetime] = mapped_column(DateTime)
    claim_type: Mapped[str] = mapped_column(String)
    claimed_amount: Mapped[float] = mapped_column(Float)
    approved_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus), default=ClaimStatus.SUBMITTED)

    policy = relationship("Policy", back_populates="claims")

class Underwriting(Base):
    __tablename__ = "underwritings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_id: Mapped[int] = mapped_column(Integer, ForeignKey("policies.id"))
    risk_score: Mapped[float] = mapped_column(Float)
    factors: Mapped[Dict] = mapped_column(JSON)
    decision: Mapped[UnderwritingDecision] = mapped_column(Enum(UnderwritingDecision))
    premium_adjustment: Mapped[float] = mapped_column(Float, default=0.0)

    policy = relationship("Policy", back_populates="underwriting")
