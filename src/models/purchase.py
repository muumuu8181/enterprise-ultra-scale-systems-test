from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = (
        {"postgresql_partition_by": "RANGE (created_at)"},
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency_added: Mapped[int] = mapped_column(Integer, nullable=False)
    receipt_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
