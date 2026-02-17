from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class MatchMode(str, PyEnum):
    RANKED = "ranked"
    CASUAL = "casual"

class MatchStatus(str, PyEnum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Using UUID string or generated ID
    player1_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    player2_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    mode: Mapped[MatchMode] = mapped_column(Enum(MatchMode), nullable=False)
    winner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), default=MatchStatus.PENDING)
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PlayerRating(Base):
    __tablename__ = "player_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    mode: Mapped[MatchMode] = mapped_column(Enum(MatchMode), nullable=False)
    elo_rating: Mapped[int] = mapped_column(Integer, default=1200)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
