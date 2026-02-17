from datetime import datetime
from enum import Enum
from typing import Optional, Any, Dict
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base

class QuestType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    STORY = "story"

class QuestStatus(str, Enum):
    INACTIVE = "inactive"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    CLAIMED = "claimed"

class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[QuestType] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    rewards: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    reset_interval: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class UserQuest(Base):
    __tablename__ = "user_quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id"), nullable=False)
    status: Mapped[QuestStatus] = mapped_column(String, default=QuestStatus.INACTIVE, nullable=False)
    progress: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
