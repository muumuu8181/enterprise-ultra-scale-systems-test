from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SAEnum, JSON, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"

class MetricType(str, Enum):
    API_CALLS = "api_calls"
    STORAGE = "storage"
    USERS = "users"

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    plan_id = Column(String, nullable=False)
    billing_cycle = Column(SAEnum(BillingCycle), nullable=False)
    next_billing_date = Column(DateTime, nullable=True)
    stripe_sub_id = Column(String, nullable=True)

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    period = Column(String, nullable=False) # e.g., "2023-10"
    line_items = Column(JSON, nullable=True)
    subtotal = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    paid_at = Column(DateTime, nullable=True)
    stripe_invoice_id = Column(String, nullable=True)

class UsageAlert(Base):
    __tablename__ = "usage_alerts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    metric = Column(SAEnum(MetricType), nullable=False)
    threshold_pct = Column(Float, nullable=False)
    triggered_at = Column(DateTime, nullable=True)
    notified = Column(Boolean, default=False)
