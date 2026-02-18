from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.learning_models import LearnerProfile, LearningPath, Assessment
from src.services.adaptive_service import generate_learning_path, select_next_question, update_knowledge_graph, Question
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

router = APIRouter(prefix="/learning", tags=["learning"])

# Pydantic Models

class LearnerProfileResponse(BaseModel):
    id: int
    user_id: str
    learning_style: str
    knowledge_graph: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    model_config = ConfigDict(from_attributes=True)

class LearningPathResponse(BaseModel):
    id: int
    learner_id: int
    goal: str
    modules: List[Dict[str, Any]]
    current_module: str
    completion_pct: float
    adaptive_adjusted_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class GeneratePathRequest(BaseModel):
    learner_id: int
    goal: str

class StartAssessmentRequest(BaseModel):
    learner_id: int

class AssessmentSubmitRequest(BaseModel):
    learner_id: int
    answers: Dict[str, int] # question_id -> selected_option_index

class AssessmentResult(BaseModel):
    score: float
    passed: bool
    feedback: str

# Endpoints

@router.get("/learners/{learner_id}/recommended-path", response_model=LearningPathResponse)
async def get_recommended_path(learner_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get the recommended learning path for a learner.
    """
    # Find the most recent active path
    result = await db.execute(select(LearningPath).where(LearningPath.learner_id == learner_id).order_by(LearningPath.id.desc()))
    path = result.scalars().first()
    if not path:
        raise HTTPException(status_code=404, detail="No learning path found")
    return path

@router.post("/learning-paths/generate", response_model=LearningPathResponse)
async def create_learning_path(request: GeneratePathRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate a new adaptive learning path.
    """
    path = await generate_learning_path(db, request.learner_id, request.goal)
    return path

@router.get("/modules/{module_id}/next-content")
async def get_next_content(module_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the next content (video, text, etc.) for a module.
    """
    # Mock logic: return a lecture or exercise
    return {"type": "video", "url": "http://example.com/video", "title": "Next Concept", "module_id": module_id}

@router.post("/assessments/{assessment_id}/start", response_model=Question)
async def start_assessment(assessment_id: int, request: StartAssessmentRequest, db: AsyncSession = Depends(get_db)):
    """
    Start an assessment and get the first question (adaptive).
    """
    # In reality, might create an assessment session.
    # Here, just return the first question using adaptive service.
    question = await select_next_question(db, assessment_id, request.learner_id)
    return question

@router.post("/assessments/{assessment_id}/submit", response_model=AssessmentResult)
async def submit_assessment(assessment_id: int, request: AssessmentSubmitRequest, db: AsyncSession = Depends(get_db)):
    """
    Submit assessment answers and get results. Updates knowledge graph.
    """
    # Calculate score (Mock)
    # In a real app, we would grade the answers against stored correct options.
    score = 0.85 # Mock score
    passed = score >= 0.6

    # Update knowledge graph
    result_data = {
        "score": score,
        "topics": ["general"] # Mock topics, normally derived from assessment metadata
    }
    await update_knowledge_graph(db, request.learner_id, result_data)

    return AssessmentResult(score=score, passed=passed, feedback="Great job! You demonstrated strong understanding.")

@router.get("/learners/{learner_id}/progress")
async def get_learner_progress(learner_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get the learner's overall progress.
    """
    result = await db.execute(select(LearningPath).where(LearningPath.learner_id == learner_id))
    paths = result.scalars().all()

    total_paths = len(paths)
    avg_completion = sum([p.completion_pct for p in paths]) / total_paths if total_paths > 0 else 0.0

    return {
        "learner_id": learner_id,
        "active_paths": total_paths,
        "overall_completion": avg_completion
    }
