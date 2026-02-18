from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import JSON
from src.database import Base
from datetime import datetime
from typing import List, Optional, Dict

class LearnerProfile(Base):
    """
    Learner Profile Model
    """
    __tablename__ = "learner_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    learning_style: Mapped[str] = mapped_column(String) # visual/auditory/kinesthetic
    knowledge_graph: Mapped[Dict] = mapped_column(JSON, default={})
    strengths: Mapped[List[str]] = mapped_column(JSON, default=[])
    weaknesses: Mapped[List[str]] = mapped_column(JSON, default=[])

    learning_paths: Mapped[List["LearningPath"]] = relationship("LearningPath", back_populates="learner")

class LearningPath(Base):
    """
    Learning Path Model
    """
    __tablename__ = "learning_paths"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, ForeignKey("learner_profiles.id"))
    goal: Mapped[str] = mapped_column(String)
    modules: Mapped[List[Dict]] = mapped_column(JSON, default=[])
    current_module: Mapped[str] = mapped_column(String)
    completion_pct: Mapped[float] = mapped_column(Float, default=0.0)
    adaptive_adjusted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    learner: Mapped["LearnerProfile"] = relationship("LearnerProfile", back_populates="learning_paths")

class Assessment(Base):
    """
    Assessment Model
    """
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    module_id: Mapped[str] = mapped_column(String, index=True)
    question_bank_size: Mapped[int] = mapped_column(Integer)
    passing_score: Mapped[float] = mapped_column(Float)
    adaptive_difficulty: Mapped[bool] = mapped_column(Boolean, default=True)
    time_limit_min: Mapped[int] = mapped_column(Integer)
