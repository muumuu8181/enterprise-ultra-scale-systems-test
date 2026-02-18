from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Boolean, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timezone

from src.database import Base

class AccountType(enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    CRYPTO = "crypto"

class TransactionType(enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class BudgetPeriod(enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    account_name = Column(String, nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    balance = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    institution = Column(String, nullable=True)

    transactions = relationship("Transaction", back_populates="account")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    merchant = Column(String, nullable=True)
    category = Column(String, nullable=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)

    account = relationship("Account", back_populates="transactions")

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    period = Column(Enum(BudgetPeriod), default=BudgetPeriod.MONTHLY)
    category = Column(String, nullable=False)
    allocated = Column(Float, default=0.0)
    spent = Column(Float, default=0.0)
    rollover_enabled = Column(Boolean, default=False)
