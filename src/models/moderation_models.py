from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"

class Decision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"

class ContentSubmission(BaseModel):
    id: str
    content_type: ContentType
    source_platform: str
    submitted_by: str
    content_uri: str
    language: Optional[str] = None

class ModerationDecision(BaseModel):
    id: str
    submission_id: str
    decision: Decision
    confidence: float
    rule_triggered: Optional[str] = None
    model_version: str
    processing_ms: int

class AppealCase(BaseModel):
    id: str
    decision_id: str
    appellant_id: str
    reason: str
    evidence: Dict[str, Any]
    reviewed_by: Optional[str] = None
    final_decision: Optional[Decision] = None

class ClassificationResult(BaseModel):
    flagged: bool
    category: Optional[str] = None
    confidence: float

class ImageModerationResult(BaseModel):
    flagged: bool
    labels: List[str]
    confidence: float
