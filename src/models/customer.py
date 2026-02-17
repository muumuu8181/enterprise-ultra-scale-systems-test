from sqlalchemy import String, Text, UUID, Boolean, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import TimestampMixin
from ..core.database import Base
import uuid

class Customer(Base, TimestampMixin):
    """
    顧客モデル (Customer Domain)
    docs/STEP2_DATABASE.md の customers テーブルに対応
    """
    __tablename__ = "customers"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    tax_id: Mapped[str | None] = mapped_column(String(50), unique=True)
    kyc_status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING, VERIFIED, REJECTED

    # Relationships
    accounts = relationship("Account", back_populates="customer", cascade="all, delete-orphan")
