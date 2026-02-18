from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.models.base import Base
from datetime import datetime

class GlobalLeaderboard(Base):
    __tablename__ = "global_leaderboards"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, index=True)
    period = Column(String)  # daily/weekly/alltime
    last_updated = Column(DateTime, default=datetime.utcnow)

    entries = relationship("LeaderboardEntry", back_populates="leaderboard", cascade="all, delete-orphan")

class LeaderboardEntry(Base):
    __tablename__ = "leaderboard_entries"

    id = Column(Integer, primary_key=True, index=True)
    leaderboard_id = Column(Integer, ForeignKey("global_leaderboards.id"))
    player_id = Column(String, index=True)
    score = Column(Float)
    rank = Column(Integer)
    rank_change = Column(Integer, default=0)
    # Using 'meta_data' to avoid conflict with SQLAlchemy's internal 'metadata' attribute
    meta_data = Column("metadata", JSON, nullable=True)

    leaderboard = relationship("GlobalLeaderboard", back_populates="entries")

class PlayerStats(Base):
    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String, index=True)
    game_id = Column(String, index=True)
    total_playtime_hrs = Column(Float, default=0.0)
    highest_score = Column(Float, default=0.0)
    matches_won = Column(Integer, default=0)
    matches_lost = Column(Integer, default=0)
