from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class PaymentMethod(Base):
    """
    支払い方法モデル
    """
    __tablename__ = 'payment_methods'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    type = Column(String, nullable=False)  # card/bank/wallet
    details_encrypted = Column(String, nullable=False)
    is_default = Column(Boolean, default=False)

class Transaction(Base):
    """
    取引モデル
    """
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    payer_id = Column(String, index=True, nullable=False)
    payee_id = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    method_id = Column(Integer, ForeignKey('payment_methods.id'), nullable=False)
    status = Column(String, nullable=False, default='PENDING')
    idempotency_key = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    payment_method = relationship("PaymentMethod")

class Refund(Base):
    """
    返金モデル
    """
    __tablename__ = 'refunds'

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, nullable=False, default='PENDING')
    initiated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    transaction = relationship("Transaction")

class Dispute(Base):
    """
    紛争モデル
    """
    __tablename__ = 'disputes'

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    reason = Column(String, nullable=False)
    evidence = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default='OPEN')
    resolution = Column(String, nullable=True)

    transaction = relationship("Transaction")
