from __future__ import annotations
import enum
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SAEnum, JSON, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class TierLevel(str, enum.Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"

class TransactionType(str, enum.Enum):
    EARN = "earn"
    REDEEM = "redeem"
    EXPIRE = "expire"
    ADJUST = "adjust"

class LoyaltyMember(Base):
    __tablename__ = "loyalty_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    program_id: Mapped[str] = mapped_column(String, nullable=False)
    tier: Mapped[TierLevel] = mapped_column(SAEnum(TierLevel), default=TierLevel.BRONZE, nullable=False)
    points_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    transactions: Mapped[list["PointsTransaction"]] = relationship(back_populates="member")

class PointsTransaction(Base):
    __tablename__ = "points_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("loyalty_members.id"), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    member: Mapped["LoyaltyMember"] = relationship(back_populates="transactions")

class LoyaltyTier(Base):
    __tablename__ = "loyalty_tiers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    program_id: Mapped[str] = mapped_column(String, nullable=False)
    tier_name: Mapped[TierLevel] = mapped_column(SAEnum(TierLevel), nullable=False)
    min_points: Mapped[int] = mapped_column(Integer, nullable=False)
    benefits: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    multiplier: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
