from sqlalchemy import String, Numeric, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import TimestampMixin
from ..core.database import Base
import uuid
from decimal import Decimal

class Account(Base, TimestampMixin):
    """
    口座モデル (Account Domain)
    docs/STEP2_DATABASE.md の accounts テーブルに対応
    """
    __tablename__ = "accounts"

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.customer_id"), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20))  # SAVINGS, CURRENT, etc.
    currency: Mapped[str] = mapped_column(String(3), default="JPY")
    balance: Mapped[Decimal] = mapped_column(Numeric(19, 4), default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE, FROZEN, CLOSED

    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    transaction_entries = relationship("TransactionEntry", back_populates="account")
