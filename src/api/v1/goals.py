from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from datetime import datetime

from src.database import get_db
from src.models.goals_models import FinancialGoal, GoalType
from src.services import planning_service
from src.schemas.planning_schemas import SavingsPlan

router = APIRouter(prefix="/goals", tags=["goals"])

class GoalCreate(BaseModel):
    user_id: int
    goal_type: GoalType
    target_amount: float
    deadline: datetime
    monthly_contribution: float

@router.post("/create", response_model=dict)
async def create_goal(goal: GoalCreate, db: AsyncSession = Depends(get_db)):
    db_goal = FinancialGoal(
        user_id=goal.user_id,
        goal_type=goal.goal_type,
        target_amount=goal.target_amount,
        deadline=goal.deadline,
        monthly_contribution=goal.monthly_contribution
    )
    db.add(db_goal)
    await db.commit()
    await db.refresh(db_goal)
    return {"id": db_goal.id, "status": "created"}

@router.get("/{id}/progress")
async def get_goal_progress(id: int, db: AsyncSession = Depends(get_db)):
    goal = await db.get(FinancialGoal, id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    progress = (goal.current_amount / goal.target_amount) * 100 if goal.target_amount > 0 else 0
    return {
        "id": goal.id,
        "current_amount": goal.current_amount,
        "target_amount": goal.target_amount,
        "progress_percentage": progress
    }

@router.get("/{id}/savings-plan", response_model=SavingsPlan)
async def get_savings_plan(id: int):
    plan = await planning_service.generate_savings_plan(id)
    return plan

@router.get("/recommendations")
async def get_recommendations():
    return {"message": "General financial recommendations based on profile"}
