from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import String, Numeric, DateTime, Integer, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

class ConnectionStatus(str, PyEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"

class AccountType(str, PyEnum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"

class BankConnection(Base):
    __tablename__ = "bank_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    bank_name: Mapped[str] = mapped_column(String, nullable=False)
    access_token: Mapped[str] = mapped_column(String, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    scope: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ConnectionStatus] = mapped_column(Enum(ConnectionStatus), default=ConnectionStatus.ACTIVE, nullable=False)

    # Relationships
    accounts: Mapped[List["BankAccount"]] = relationship(back_populates="connection", cascade="all, delete-orphan")

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    connection_id: Mapped[int] = mapped_column(ForeignKey("bank_connections.id"), nullable=False)
    account_number_hash: Mapped[str] = mapped_column(String, nullable=False)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    connection: Mapped["BankConnection"] = relationship(back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="account", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("bank_accounts.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    merchant: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    enriched_category: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    account: Mapped["BankAccount"] = relationship(back_populates="transactions")
