from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.db.base import Base

class PortfolioType(str, Enum):
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    MIXED = "mixed"

class AssetType(str, Enum):
    STOCK = "stock"
    BOND = "bond"
    DERIVATIVE = "derivative"
    FX = "fx"

class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(index=True)
    portfolio_type: Mapped[PortfolioType] = mapped_column(SAEnum(PortfolioType))
    total_value: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    last_valued_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    positions: Mapped[List["Position"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")
    risk_metrics: Mapped[List["RiskMetric"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")

class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"))
    asset_id: Mapped[str] = mapped_column(String, index=True)
    asset_type: Mapped[AssetType] = mapped_column(SAEnum(AssetType))
    quantity: Mapped[float] = mapped_column(Float)
    avg_cost: Mapped[float] = mapped_column(Float)
    current_value: Mapped[float] = mapped_column(Float)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="positions")

class RiskMetric(Base):
    __tablename__ = "risk_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"))
    calculated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    var_95: Mapped[float] = mapped_column(Float)
    var_99: Mapped[float] = mapped_column(Float)
    cvar_95: Mapped[float] = mapped_column(Float)
    sharpe_ratio: Mapped[float] = mapped_column(Float)
    max_drawdown: Mapped[float] = mapped_column(Float)
    beta: Mapped[float] = mapped_column(Float)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="risk_metrics")
