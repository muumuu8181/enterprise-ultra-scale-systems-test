from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.rl_models import TrainingTask, Policy, Curriculum, TrainingAlgorithm
from src.services.rl_service import run_training_step, evaluate_policy, generate_curriculum, TrainingMetrics, EvalResult
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional

class TrainingTaskCreate(BaseModel):
    sim_id: str
    robot_id: str
    objective: Dict[str, Any]
    algorithm: TrainingAlgorithm
    max_episodes: int

class TrainingTaskRead(BaseModel):
    id: int
    sim_id: str
    robot_id: str
    objective: Dict[str, Any]
    algorithm: TrainingAlgorithm
    max_episodes: int
    reward_history: List[float]
    current_episode: int
    model_config = ConfigDict(from_attributes=True)

class PolicyCreate(BaseModel):
    task_id: int
    neural_network_config: Dict[str, Any]
    weights_uri: str
    checkpoint_episode: int

class PolicyRead(BaseModel):
    id: int
    task_id: int
    neural_network_config: Dict[str, Any]
    weights_uri: str
    eval_score: Optional[float]
    checkpoint_episode: int
    model_config = ConfigDict(from_attributes=True)

class CurriculumCreate(BaseModel):
    name: str
    task_sequence: List[Dict[str, Any]]
    auto_advance_threshold: float

class CurriculumRead(BaseModel):
    id: int
    name: str
    task_sequence: List[Dict[str, Any]]
    auto_advance_threshold: float
    current_stage: int
    model_config = ConfigDict(from_attributes=True)

router_training = APIRouter(prefix="/training", tags=["training"])
router_policies = APIRouter(prefix="/policies", tags=["policies"])
router_curriculum = APIRouter(prefix="/curriculum", tags=["curriculum"])

@router_training.post("/tasks/create", response_model=TrainingTaskRead)
async def create_training_task(task: TrainingTaskCreate, db: AsyncSession = Depends(get_db)):
    db_task = TrainingTask(**task.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

@router_training.get("/tasks/{id}/progress", response_model=TrainingTaskRead)
async def get_training_progress(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingTask).where(TrainingTask.id == id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router_policies.get("/{id}/evaluate", response_model=EvalResult)
async def evaluate_policy_endpoint(id: int, n_episodes: int = 5, db: AsyncSession = Depends(get_db)):
    try:
        result = await evaluate_policy(id, n_episodes, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router_policies.post("/{id}/deploy")
async def deploy_policy(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Policy).where(Policy.id == id))
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    # Mock deployment
    return {"status": "deployed", "policy_id": id}

@router_curriculum.get("/{id}/status", response_model=CurriculumRead)
async def get_curriculum_status(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Curriculum).where(Curriculum.id == id))
    curr = result.scalars().first()
    if not curr:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    return curr

@router_curriculum.post("/{id}/advance")
async def advance_curriculum(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Curriculum).where(Curriculum.id == id))
    curr = result.scalars().first()
    if not curr:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    curr.current_stage += 1
    await db.commit()
    await db.refresh(curr)
    return {"status": "advanced", "current_stage": curr.current_stage}
