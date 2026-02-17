from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.core.database import get_db
from src.models.assignment_models import Assignment, Submission, PeerReview
from src.schemas.assignment_schemas import (
    AssignmentCreate, AssignmentResponse, SubmissionCreate, SubmissionResponse,
    PeerReviewCreate, PeerReviewResponse
)
from src.services.grading_service import auto_grade_code, check_plagiarism, ai_feedback

router = APIRouter(prefix="/assignments", tags=["assignments"])

@router.post("/create", response_model=AssignmentResponse)
async def create_assignment(assignment: AssignmentCreate, db: AsyncSession = Depends(get_db)):
    new_assignment = Assignment(**assignment.model_dump())
    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)
    return new_assignment

@router.get("/{id}/submissions", response_model=List[SubmissionResponse])
async def get_submissions(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Submission).filter(Submission.assignment_id == id))
    submissions = result.scalars().all()
    return submissions

@router.post("/{id}/submit", response_model=SubmissionResponse)
async def submit_assignment(id: int, submission: SubmissionCreate, db: AsyncSession = Depends(get_db)):
    new_submission = Submission(assignment_id=id, **submission.model_dump())
    db.add(new_submission)
    await db.commit()
    await db.refresh(new_submission)

    # Trigger automated checks
    grade_result = await auto_grade_code(new_submission.id)
    plagiarism = await check_plagiarism(new_submission.id)
    feedback_ai = await ai_feedback(new_submission.id)

    new_submission.grade = grade_result.score
    new_submission.feedback = f"{grade_result.feedback}\nAI Feedback: {feedback_ai}"
    new_submission.plagiarism_score = plagiarism
    await db.commit()
    await db.refresh(new_submission)

    return new_submission

@router.get("/{id}/my-submission", response_model=SubmissionResponse)
async def get_my_submission(id: int, student_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Submission).filter(Submission.assignment_id == id, Submission.student_id == student_id)
    )
    submission = result.scalars().first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission

@router.post("/{id}/grade/{submission_id}", response_model=SubmissionResponse)
async def grade_submission(id: int, submission_id: int, grade: float, feedback: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Submission).filter(Submission.id == submission_id, Submission.assignment_id == id))
    submission = result.scalars().first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    submission.grade = grade
    submission.feedback = feedback
    await db.commit()
    await db.refresh(submission)
    return submission

@router.post("/{id}/peer-review", response_model=PeerReviewResponse)
async def create_peer_review(id: int, review: PeerReviewCreate, db: AsyncSession = Depends(get_db)):
    # Check if submission belongs to assignment
    result = await db.execute(select(Submission).filter(Submission.id == review.submission_id, Submission.assignment_id == id))
    submission = result.scalars().first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found or does not belong to assignment")

    new_review = PeerReview(**review.model_dump())
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review
