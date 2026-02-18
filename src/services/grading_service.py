from celery import Celery
from src.core.config import settings
from src.schemas.assignment_schemas import GradeResult
import asyncio
import random

celery_app = Celery(
    "grading",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

async def auto_grade_code(submission_id: int) -> GradeResult:
    """Mock implementation for grading code."""
    await asyncio.sleep(1)  # Simulate processing
    return GradeResult(score=random.uniform(70, 100), feedback="Code compiles and passes basic tests.")

async def check_plagiarism(submission_id: int) -> float:
    """Mock implementation for checking plagiarism."""
    await asyncio.sleep(1)  # Simulate processing
    return random.uniform(0, 10)  # 0-10% plagiarism

async def ai_feedback(submission_id: int) -> str:
    """Mock implementation for AI feedback."""
    await asyncio.sleep(1)  # Simulate processing
    return "Good structure, but variable naming could be improved."
