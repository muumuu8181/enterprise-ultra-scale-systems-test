from sqlalchemy import String, Integer, BigInteger, ForeignKey, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Chapter(Base):
    """
    ストーリーの章を表すモデル
    """
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    unlock_conditions: Mapped[dict] = mapped_column(JSON, nullable=True)  # 解放条件
    rewards: Mapped[dict] = mapped_column(JSON, nullable=True)  # 章クリア報酬

    stages: Mapped[list["Stage"]] = relationship("Stage", back_populates="chapter", cascade="all, delete-orphan")

class Stage(Base):
    """
    ストーリーのステージを表すモデル
    """
    __tablename__ = "stages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(Integer, ForeignKey("chapters.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    recommended_power: Mapped[int] = mapped_column(Integer, default=0)
    star_conditions: Mapped[dict] = mapped_column(JSON, nullable=True)  # 星獲得条件 (e.g. {"time": 60, "hp": 80})

    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="stages")
    user_progress: Mapped[list["UserStageProgress"]] = relationship("UserStageProgress", back_populates="stage")

class UserStageProgress(Base):
    """
    ユーザーのステージ進捗を表すモデル
    """
    __tablename__ = "user_stage_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "stage_id", name="uq_user_stage_progress"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    stage_id: Mapped[int] = mapped_column(Integer, ForeignKey("stages.id"), nullable=False)
    cleared: Mapped[bool] = mapped_column(Boolean, default=False)
    stars: Mapped[int] = mapped_column(Integer, default=0)  # 獲得した星の数 (0-3)
    best_score: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)

    stage: Mapped["Stage"] = relationship("Stage", back_populates="user_progress")
