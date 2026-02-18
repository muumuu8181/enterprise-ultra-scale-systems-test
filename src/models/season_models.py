from datetime import datetime
from typing import Optional, List, Any, Dict
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base

class Season(Base):
    """
    シーズン情報のモデル
    Model for Season information
    """
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    max_stages: Mapped[int] = mapped_column(Integer, nullable=False)
    premium_price: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    stages: Mapped[List["SeasonStage"]] = relationship("SeasonStage", back_populates="season", cascade="all, delete-orphan")
    user_seasons: Mapped[List["UserSeason"]] = relationship("UserSeason", back_populates="season")


class SeasonStage(Base):
    """
    シーズンステージ情報のモデル (各レベルの報酬など)
    Model for Season Stage information (rewards for each level)
    """
    __tablename__ = "season_stages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), nullable=False)
    stage_number: Mapped[int] = mapped_column(Integer, nullable=False)
    required_xp: Mapped[int] = mapped_column(Integer, nullable=False) # Cumulative XP required to reach this stage
    free_reward: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    premium_reward: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)

    # Relationships
    season: Mapped["Season"] = relationship("Season", back_populates="stages")


class UserSeason(Base):
    """
    ユーザーのシーズン進捗状況
    User's season progress
    """
    __tablename__ = "user_seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), nullable=False)
    current_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_stages: Mapped[List[int]] = mapped_column(JSON, default=list, nullable=False) # List of stage numbers claimed

    # Relationships
    season: Mapped["Season"] = relationship("Season", back_populates="user_seasons")
