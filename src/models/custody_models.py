from sqlalchemy import String, Integer, Float, Boolean, JSON, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from src.database import Base

class CustodyType(str, enum.Enum):
    hot = "hot"
    warm = "warm"
    cold = "cold"

class Blockchain(str, enum.Enum):
    bitcoin = "bitcoin"
    ethereum = "ethereum"
    solana = "solana"

class TxType(str, enum.Enum):
    deposit = "deposit"
    withdrawal = "withdrawal"
    sweep = "sweep"

class TxStatus(str, enum.Enum):
    pending = "pending"
    signed = "signed"
    broadcast = "broadcast"
    confirmed = "confirmed"
    failed = "failed"

class Vault(Base):
    __tablename__ = "vaults"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    custody_type: Mapped[CustodyType] = mapped_column(SAEnum(CustodyType))
    blockchain: Mapped[Blockchain] = mapped_column(SAEnum(Blockchain))
    address: Mapped[str] = mapped_column(String, unique=True, index=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    multi_sig_threshold: Mapped[int] = mapped_column(Integer, default=1)
    signers: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions = relationship("Transaction", back_populates="vault")
    policies = relationship("ApprovalPolicy", back_populates="vault")

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vault_id: Mapped[int] = mapped_column(ForeignKey("vaults.id"))
    tx_type: Mapped[TxType] = mapped_column(SAEnum(TxType))
    amount: Mapped[float] = mapped_column(Float)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    tx_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    confirmations: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[TxStatus] = mapped_column(SAEnum(TxStatus), default=TxStatus.pending)
    initiated_by: Mapped[str] = mapped_column(String) # User ID or name

    vault = relationship("Vault", back_populates="transactions")

class ApprovalPolicy(Base):
    __tablename__ = "approval_policies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vault_id: Mapped[int] = mapped_column(ForeignKey("vaults.id"))
    min_approvers: Mapped[int] = mapped_column(Integer, default=1)
    max_amount_without_approval: Mapped[float] = mapped_column(Float, default=0.0)
    whitelist_addresses: Mapped[list] = mapped_column(JSON, default=[])
    time_lock_hours: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    vault = relationship("Vault", back_populates="policies")
