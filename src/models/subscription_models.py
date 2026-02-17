from enum import Enum as PyEnum
from typing import List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, Enum, JSON, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel, ConfigDict

class Base(DeclarativeBase):
    pass

class PlanInterval(str, PyEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"

class SubscriptionStatus(str, PyEnum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"

class UsageMetric(str, PyEnum):
    API_CALLS = "api_calls"
    STORAGE_GB = "storage_gb"
    SEATS = "seats"

class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    interval: Mapped[PlanInterval] = mapped_column(Enum(PlanInterval))
    price: Mapped[float] = mapped_column(Float)
    trial_days: Mapped[int] = mapped_column(Integer, default=0)
    features: Mapped[dict] = mapped_column(JSON)
    usage_limits: Mapped[dict] = mapped_column(JSON)

    subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="plan")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(100))
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIALING)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    stripe_sub_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    plan: Mapped["Plan"] = relationship(back_populates="subscriptions")
    usage_records: Mapped[List["UsageRecord"]] = relationship(back_populates="subscription")

class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"))
    metric: Mapped[UsageMetric] = mapped_column(Enum(UsageMetric))
    quantity: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    billable: Mapped[bool] = mapped_column(Boolean, default=True)

    subscription: Mapped["Subscription"] = relationship(back_populates="usage_records")

# Pydantic models for service return types
class Invoice(BaseModel):
    id: str
    subscription_id: int
    amount_due: float
    currency: str
    status: str
    period_start: datetime
    period_end: datetime
    model_config = ConfigDict(from_attributes=True)

class ProrationResult(BaseModel):
    old_plan_id: int
    new_plan_id: int
    prorated_amount: float
    credit_applied: float
    amount_due: float
