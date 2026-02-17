from sqlalchemy import Integer, String, Float, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from datetime import datetime, timezone
import enum

class TransferType(str, enum.Enum):
    PERMANENT = "permanent"
    LOAN = "loan"

class ScoutReport(Base):
    __tablename__ = "scout_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scout_id: Mapped[str] = mapped_column(String, index=True)
    player_id: Mapped[str] = mapped_column(String, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    skills: Mapped[dict] = mapped_column(JSON)
    physical_ratings: Mapped[dict] = mapped_column(JSON)
    recommendation: Mapped[str] = mapped_column(String)
    market_value_estimate: Mapped[float] = mapped_column(Float)

class TransferMarket(Base):
    __tablename__ = "transfer_market"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    player_id: Mapped[str] = mapped_column(String, index=True)
    from_club_id: Mapped[str] = mapped_column(String)
    to_club_id: Mapped[str] = mapped_column(String)
    fee: Mapped[float] = mapped_column(Float)
    contract_years: Mapped[float] = mapped_column(Float)
    announced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    transfer_type: Mapped[TransferType] = mapped_column(Enum(TransferType))

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    player_id: Mapped[str] = mapped_column(String, index=True)
    match_id: Mapped[str] = mapped_column(String)
    position: Mapped[str] = mapped_column(String)
    distance_km: Mapped[float] = mapped_column(Float)
    sprints: Mapped[int] = mapped_column(Integer)
    passes_accurate: Mapped[int] = mapped_column(Integer)
    goals: Mapped[int] = mapped_column(Integer)
    assists: Mapped[int] = mapped_column(Integer)
    rating: Mapped[float] = mapped_column(Float)
