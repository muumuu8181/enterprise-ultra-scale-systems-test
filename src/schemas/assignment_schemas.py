from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime
from enum import Enum

class SubmissionType(str, Enum):
    FILE = "file"
    CODE = "code"
    ESSAY = "essay"

class AssignmentCreate(BaseModel):
    class_id: int
    title: str
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None
    max_points: int
    rubric: Optional[Dict[str, Any]] = None
    submission_type: SubmissionType

class AssignmentResponse(AssignmentCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class SubmissionCreate(BaseModel):
    student_id: int
    content_uri: str

class SubmissionResponse(SubmissionCreate):
    id: int
    assignment_id: int
    submitted_at: datetime
    grade: Optional[float] = None
    feedback: Optional[str] = None
    plagiarism_score: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class PeerReviewCreate(BaseModel):
    submission_id: int
    reviewer_id: int
    scores: Dict[str, float]
    feedback: str

class PeerReviewResponse(PeerReviewCreate):
    id: int
    submission_id: int
    reviewed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class GradeResult(BaseModel):
    score: float
    feedback: str
