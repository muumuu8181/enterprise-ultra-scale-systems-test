from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.database import get_db
from src.models.hr_models import PerformanceReview, PerformanceGoal, Employee
from src.schemas.hr_schemas import PerformanceReviewResponse, PerformanceGoalResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import date

router = APIRouter(prefix="/performance", tags=["performance"])

class ReviewRequest(BaseModel):
    employee_id: int
    period: str
    ratings: Dict[str, int]
    comments: str

class Goal(BaseModel):
    description: str
    deadline: date

class GoalsRequest(BaseModel):
    employee_id: int
    goals: List[Goal]

@router.post("/reviews", response_model=PerformanceReviewResponse)
async def create_review(request: ReviewRequest, db: AsyncSession = Depends(get_db)):
    # Check employee
    result = await db.execute(select(Employee).where(Employee.id == request.employee_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Employee not found")

    review = PerformanceReview(
        employee_id=request.employee_id,
        period=request.period,
        ratings=request.ratings,
        comments=request.comments
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review

@router.get("/{employee_id}/history", response_model=List[PerformanceReviewResponse])
async def get_history(employee_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PerformanceReview).where(PerformanceReview.employee_id == employee_id))
    reviews = result.scalars().all()
    return reviews

@router.post("/goals", response_model=List[PerformanceGoalResponse])
async def create_goals(request: GoalsRequest, db: AsyncSession = Depends(get_db)):
    # Check employee
    result = await db.execute(select(Employee).where(Employee.id == request.employee_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Employee not found")

    created_goals = []
    for goal_req in request.goals:
        goal = PerformanceGoal(
            employee_id=request.employee_id,
            description=goal_req.description,
            deadline=goal_req.deadline
        )
        db.add(goal)
        created_goals.append(goal)

    await db.commit()
    for goal in created_goals:
        await db.refresh(goal)

    return created_goals
