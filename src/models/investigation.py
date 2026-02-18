import enum
from sqlalchemy import Column, Integer, String, Enum, Float, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func
from src.core.database import Base

class FraudCaseType(enum.Enum):
    ACCOUNT_TAKEOVER = "account_takeover"
    SYNTHETIC_ID = "synthetic_id"
    PAYMENT_FRAUD = "payment_fraud"

class FraudCaseStatus(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"

class ChargebackStatus(enum.Enum):
    RECEIVED = "received"
    WON = "won"
    LOST = "lost"

class FraudCase(Base):
    __tablename__ = "fraud_cases"

    id = Column(Integer, primary_key=True, index=True)
    transaction_ids = Column(JSON)
    case_type = Column(Enum(FraudCaseType))
    status = Column(Enum(FraudCaseStatus), default=FraudCaseStatus.OPEN)
    estimated_loss = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class InvestigationNote(Base):
    __tablename__ = "investigation_notes"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("fraud_cases.id"))
    investigator_id = Column(String)
    note = Column(String)
    evidence = Column(JSON)
    action_taken = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Chargeback(Base):
    __tablename__ = "chargebacks"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, index=True)
    reason_code = Column(String)
    dispute_amount = Column(Float)
    status = Column(Enum(ChargebackStatus), default=ChargebackStatus.RECEIVED)
    bank_response = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
