import enum
from sqlalchemy import Column, Integer, String, Float, Enum, JSON
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel
from typing import Optional

Base = declarative_base()

class ActionType(str, enum.Enum):
    REMOVE = "remove"
    BLUR = "blur"
    WARN = "warn"
    REVIEW = "review"

class LabelCategory(str, enum.Enum):
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    NUDITY = "nudity"
    SPAM = "spam"
    MISINFORMATION = "misinformation"

class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    HARD = "hard"
    EDGE_CASE = "edge_case"

class ContentPolicy(Base):
    __tablename__ = "content_policies"

    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, nullable=False)
    policy_name = Column(String, nullable=False)
    categories = Column(JSON, nullable=False)
    thresholds = Column(JSON, nullable=False)
    action = Column(Enum(ActionType), nullable=False)

class ModerationLabel(Base):
    __tablename__ = "moderation_labels"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(Enum(LabelCategory), nullable=False)
    subcategory = Column(String, nullable=True)
    confidence_threshold = Column(Float, nullable=False)

class ReviewerAnnotation(Base):
    __tablename__ = "reviewer_annotations"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(String, nullable=False)
    reviewer_id = Column(String, nullable=False)
    labels = Column(JSON, nullable=False)
    difficulty = Column(Enum(DifficultyLevel), nullable=False)
    time_taken_sec = Column(Float, nullable=False)

class PolicyDecision(BaseModel):
    action: ActionType
    policy_id: int
    details: Optional[str] = None
