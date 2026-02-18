from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
import uuid
from datetime import datetime
import asyncio

from src.models.moderation_models import (
    ContentSubmission,
    ModerationDecision,
    AppealCase,
    ContentType,
    Decision,
    ClassificationResult,
    ImageModerationResult
)
from src.services.classification_service import classify_text, classify_image, detect_spam

router = APIRouter()

# In-memory storage for demo purposes
submissions_db: Dict[str, ContentSubmission] = {}
decisions_db: Dict[str, ModerationDecision] = {}
appeals_db: Dict[str, AppealCase] = {}

@router.post("/submissions/classify", response_model=ModerationDecision)
async def classify_submission(submission: ContentSubmission):
    """
    Real-time classification of a submission.
    """
    submissions_db[submission.id] = submission

    start_time = datetime.now()

    confidence = 0.0
    rule_triggered = None
    decision_enum = Decision.APPROVE

    # Process based on content type
    if submission.content_type == ContentType.TEXT:
        # In a real app, we would fetch content from content_uri if it is a URL
        result = await classify_text(submission.content_uri, submission.language or "en")
        spam_score = await detect_spam(submission.content_uri)

        if result.flagged or spam_score > 0.8:
            decision_enum = Decision.REJECT
            rule_triggered = result.category or "spam_filter"
            confidence = max(result.confidence, spam_score)
        else:
            confidence = result.confidence

    elif submission.content_type == ContentType.IMAGE:
        result = await classify_image(submission.content_uri)
        if result.flagged:
            decision_enum = Decision.REJECT
            rule_triggered = "nsfw_filter"
            confidence = result.confidence
        else:
            confidence = result.confidence

    # Randomly escalate low confidence
    if confidence < 0.6:
        decision_enum = Decision.ESCALATE

    processing_ms = int((datetime.now() - start_time).total_seconds() * 1000)

    decision = ModerationDecision(
        id=str(uuid.uuid4()),
        submission_id=submission.id,
        decision=decision_enum,
        confidence=confidence,
        rule_triggered=rule_triggered,
        model_version="v1.0.0",
        processing_ms=processing_ms
    )

    decisions_db[decision.id] = decision
    return decision

@router.post("/submissions/batch-classify", response_model=List[ModerationDecision])
async def batch_classify_submission(submissions: List[ContentSubmission]):
    """
    Batch classification of submissions.
    """
    results = []
    for submission in submissions:
        decision = await classify_submission(submission)
        results.append(decision)
    return results

@router.get("/submissions/{id}/decision", response_model=ModerationDecision)
async def get_decision(id: str):
    """
    Get the decision for a submission ID.
    """
    for decision in decisions_db.values():
        if decision.submission_id == id:
            return decision

    raise HTTPException(status_code=404, detail="Decision not found for this submission")

@router.post("/submissions/{id}/appeal", response_model=AppealCase)
async def create_appeal(id: str, appeal: AppealCase):
    """
    Create an appeal for a submission ID.
    """
    # Verify decision exists for the submission
    decision = None
    for d in decisions_db.values():
        if d.submission_id == id:
            decision = d
            break

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found for this submission")

    appeals_db[appeal.id] = appeal
    return appeal

@router.get("/queue/human-review", response_model=List[ModerationDecision])
async def get_human_review_queue():
    """
    Get items queued for human review (Escalated items).
    """
    escalated = [d for d in decisions_db.values() if d.decision == Decision.ESCALATE]
    return escalated

@router.post("/review/{id}/decide", response_model=ModerationDecision)
async def human_review_decision(id: str, decision_update: ModerationDecision):
    """
    Submit a human review decision.
    ID is the decision ID.
    """
    if id in decisions_db:
         # Update the existing decision
         decisions_db[id] = decision_update
         return decision_update

    raise HTTPException(status_code=404, detail="Decision not found")
