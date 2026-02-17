from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import String, Numeric, DateTime, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base

class OrderType(str, PyEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderStatus(str, PyEnum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"

class FXRate(Base):
    """
    外国為替レートモデル
    """
    __tablename__ = "fx_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    quote_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    bid: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    ask: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    mid: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class FXOrder(Base):
    """
    FX注文モデル
    """
    __tablename__ = "fx_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    from_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    to_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType), nullable=False)
    limit_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    executed_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
