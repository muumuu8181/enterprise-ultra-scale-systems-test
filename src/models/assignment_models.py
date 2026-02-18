from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON, Enum as SqlEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from src.core.database import Base

class SubmissionType(str, enum.Enum):
    FILE = "file"
    CODE = "code"
    ESSAY = "essay"

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, index=True)
    title = Column(String, nullable=False)
    instructions = Column(String)
    due_date = Column(DateTime(timezone=True))
    max_points = Column(Integer)
    rubric = Column(JSON)
    submission_type = Column(SqlEnum(SubmissionType), nullable=False)

    submissions = relationship("Submission", back_populates="assignment")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    student_id = Column(Integer, nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    content_uri = Column(String)
    grade = Column(Float, nullable=True)
    feedback = Column(String, nullable=True)
    plagiarism_score = Column(Float, nullable=True)

    assignment = relationship("Assignment", back_populates="submissions")
    peer_reviews = relationship("PeerReview", back_populates="submission")

class PeerReview(Base):
    __tablename__ = "peer_reviews"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    reviewer_id = Column(Integer, nullable=False)
    scores = Column(JSON)
    feedback = Column(String)
    reviewed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    submission = relationship("Submission", back_populates="peer_reviews")
