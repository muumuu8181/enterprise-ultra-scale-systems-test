from sqlalchemy import String, Numeric, ForeignKey, UUID, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import TimestampMixin
from ..core.database import Base
import uuid
from decimal import Decimal

class Transaction(Base, TimestampMixin):
    """
    取引ヘッダーモデル (Transaction Header)
    論理的な取引単位（振込、入金、出金など）を管理します。
    """
    __tablename__ = "transaction_headers"  # Specにないため新規追加 (Transaction Entryとの関係のため)

    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # DEPOSIT, WITHDRAWAL, TRANSFER
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING, COMPLETED, FAILED
    description: Mapped[str | None] = mapped_column(Text)

    # Relationships
    entries = relationship("TransactionEntry", back_populates="transaction", cascade="all, delete-orphan")


class TransactionEntry(Base, TimestampMixin):
    """
    取引明細モデル (Transaction Entry/Line)
    docs/STEP2_DATABASE.md の transactions テーブルに対応 (実体としての入出金記録)
    """
    __tablename__ = "transactions"  # Specに従い transactions テーブルを使用

    entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transaction_headers.transaction_id"), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.account_id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False) # DEBIT (出金), CREDIT (入金)

    # Relationships
    transaction = relationship("Transaction", back_populates="entries")
    account = relationship("Account", back_populates="transaction_entries")
