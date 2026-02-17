from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base

class TournamentFormat(str, Enum):
    single_elim = "single_elim"
    double_elim = "double_elim"
    round_robin = "round_robin"
    swiss = "swiss"

class TournamentStatus(str, Enum):
    registration = "registration"
    seeding = "seeding"
    in_progress = "in_progress"
    completed = "completed"

class MatchStatus(str, Enum):
    scheduled = "scheduled"
    live = "live"
    completed = "completed"

class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    game_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    format: Mapped[TournamentFormat] = mapped_column(SQLEnum(TournamentFormat))
    max_participants: Mapped[int] = mapped_column(Integer)
    entry_fee: Mapped[float] = mapped_column(Float)
    prize_pool: Mapped[float] = mapped_column(Float)
    status: Mapped[TournamentStatus] = mapped_column(SQLEnum(TournamentStatus), default=TournamentStatus.registration)
    start_date: Mapped[datetime] = mapped_column(DateTime)
    participants: Mapped[list] = mapped_column(JSON, default=list)

    matches: Mapped[List["Match"]] = relationship("Match", back_populates="tournament", cascade="all, delete-orphan")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    captain_id: Mapped[int] = mapped_column(Integer)
    members: Mapped[list] = mapped_column(JSON)
    elo_rating: Mapped[int] = mapped_column(Integer, default=1000)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    tournament_history: Mapped[list] = mapped_column(JSON, default=list)
    region: Mapped[str] = mapped_column(String, index=True)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tournament_id: Mapped[int] = mapped_column(Integer, ForeignKey("tournaments.id"))
    round_number: Mapped[int] = mapped_column(Integer)
    team_a_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("teams.id"), nullable=True)
    team_b_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("teams.id"), nullable=True)
    score_a: Mapped[int] = mapped_column(Integer, default=0)
    score_b: Mapped[int] = mapped_column(Integer, default=0)
    winner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("teams.id"), nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    stream_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[MatchStatus] = mapped_column(SQLEnum(MatchStatus), default=MatchStatus.scheduled)

    tournament: Mapped["Tournament"] = relationship("Tournament", back_populates="matches")
    team_a: Mapped[Optional["Team"]] = relationship("Team", foreign_keys=[team_a_id])
    team_b: Mapped[Optional["Team"]] = relationship("Team", foreign_keys=[team_b_id])
    winner: Mapped[Optional["Team"]] = relationship("Team", foreign_keys=[winner_id])
