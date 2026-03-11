from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.database import get_db
from src.models.goals_models import InvestmentHolding
from src.services import planning_service
from src.schemas.planning_schemas import TradeRecommendation

router = APIRouter(prefix="/investments", tags=["investments"])

@router.get("/portfolio")
async def get_portfolio(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InvestmentHolding).where(InvestmentHolding.user_id == user_id))
    holdings = result.scalars().all()
    return holdings

@router.get("/{id}/performance")
async def get_performance(id: int, db: AsyncSession = Depends(get_db)):
    # Mock performance calculation
    return {"id": id, "return_ytd": 0.05, "total_return": 0.12}

@router.get("/tax-lots")
async def get_tax_lots(user_id: int):
    # Mock tax lots
    return [{"symbol": "AAPL", "date_acquired": "2023-01-15", "cost_basis": 150.0, "quantity": 10}]

@router.get("/rebalance-suggestions", response_model=List[TradeRecommendation])
async def get_rebalance_suggestions(user_id: int):
    recommendations = await planning_service.suggest_rebalancing(user_id)
    return recommendations
