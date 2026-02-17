from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Boolean, Date
from src.core.database import Base
import enum
from datetime import datetime

class PaymentSchedule(enum.Enum):
    monthly = "monthly"
    weekly = "weekly"

class RevenueSplit(Base):
    __tablename__ = "revenue_splits"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True)
    provider_share_pct = Column(Float)
    platform_fee_pct = Column(Float)
    payment_schedule = Column(Enum(PaymentSchedule))

class ProviderPayout(Base):
    __tablename__ = "provider_payouts"
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(String, index=True)
    period = Column(Date)
    gross_revenue = Column(Float)
    platform_fee = Column(Float)
    net_payout = Column(Float)
    paid_at = Column(DateTime, nullable=True)

class APIReview(Base):
    __tablename__ = "api_reviews"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True)
    reviewer_id = Column(String, index=True)
    rating = Column(Integer)
    review_text = Column(String)
    helpful_count = Column(Integer, default=0)
    verified_subscriber = Column(Boolean, default=False)
