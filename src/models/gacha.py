from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class GachaBanner(Base):
    __tablename__ = "gacha_banners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    pool_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'standard', 'limited_char', 'limited_weapon'
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    display_priority: Mapped[int] = mapped_column(Integer, default=0)

    rates: Mapped[list["GachaRate"]] = relationship("GachaRate", back_populates="banner", cascade="all, delete-orphan")


class GachaRate(Base):
    __tablename__ = "gacha_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    banner_id: Mapped[int] = mapped_column(Integer, ForeignKey("gacha_banners.id"), nullable=False)
    item_id: Mapped[str] = mapped_column(String(50), nullable=False)
    rarity: Mapped[int] = mapped_column(Integer, nullable=False)  # 3, 4, 5
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    is_pickup: Mapped[bool] = mapped_column(Boolean, default=False)

    banner: Mapped["GachaBanner"] = relationship("GachaBanner", back_populates="rates")


class GachaLog(Base):
    __tablename__ = "gacha_logs"
    __table_args__ = (
        {"postgresql_partition_by": "RANGE (created_at)"},
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    banner_id: Mapped[int] = mapped_column(Integer, ForeignKey("gacha_banners.id"), nullable=False)
    item_id: Mapped[str] = mapped_column(String(50), nullable=False)
    rarity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class UserPityCounter(Base):
    __tablename__ = "user_pity_counters"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    pool_type: Mapped[str] = mapped_column(String(50), primary_key=True)  # Matches GachaBanner.pool_type
    pity_count: Mapped[int] = mapped_column(Integer, default=0)
    hard_pity_count: Mapped[int] = mapped_column(Integer, default=0)  # Total pulls without 5* if tracking specifically
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
