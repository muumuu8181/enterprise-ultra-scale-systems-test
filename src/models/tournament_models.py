from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from datetime import datetime, timezone
from typing import Optional, List

Base = declarative_base()

class Tournament(Base):
    """
    トーナメントモデル
    Tournament model
    """
    __tablename__ = 'tournaments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    format: Mapped[str] = mapped_column(String)  # single_elimination, double_elimination
    status: Mapped[str] = mapped_column(String, default="scheduled") # scheduled, ongoing, completed
    max_participants: Mapped[int] = mapped_column(Integer)
    prize_pool: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    participants: Mapped[List["TournamentParticipant"]] = relationship(back_populates="tournament", cascade="all, delete-orphan")
    matches: Mapped[List["TournamentMatch"]] = relationship(back_populates="tournament", cascade="all, delete-orphan")

class TournamentParticipant(Base):
    """
    トーナメント参加者モデル
    Tournament Participant model
    """
    __tablename__ = 'tournament_participants'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey('tournaments.id'))
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    tournament: Mapped["Tournament"] = relationship(back_populates="participants")

class TournamentMatch(Base):
    """
    トーナメントマッチモデル
    Tournament Match model
    """
    __tablename__ = 'tournament_matches'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey('tournaments.id'))
    round: Mapped[int] = mapped_column(Integer)
    match_number: Mapped[int] = mapped_column(Integer) # To identify match within a round
    player1_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    player2_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    winner_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    score_a: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score_b: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    tournament: Mapped["Tournament"] = relationship(back_populates="matches")
