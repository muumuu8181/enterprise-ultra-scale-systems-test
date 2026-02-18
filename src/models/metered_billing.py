from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone
import enum

Base = declarative_base()

class TierType(enum.Enum):
    flat = "flat"
    graduated = "graduated"
    volume = "volume"

class DunningResult(enum.Enum):
    succeeded = "succeeded"
    failed = "failed"

class PriceTier(Base):
    __tablename__ = "price_tiers"
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(String, index=True)
    metric = Column(String)
    tier_type = Column(Enum(TierType))
    tiers = Column(JSON)

class MeteringEvent(Base):
    __tablename__ = "metering_events"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, index=True)
    metric = Column(String)
    quantity = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    idempotency_key = Column(String, unique=True, index=True)

class DunningAttempt(Base):
    __tablename__ = "dunning_attempts"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(String, index=True)
    attempt_number = Column(Integer)
    attempted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    amount = Column(Float)
    result = Column(Enum(DunningResult))
    next_attempt_at = Column(DateTime, nullable=True)
