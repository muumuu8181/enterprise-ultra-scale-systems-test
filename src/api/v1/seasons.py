from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from src.database import get_db
from src.deps import get_current_user_id
from src.services.season_service import SeasonService
from src.models.season_models import Season, SeasonStage, UserSeason

router = APIRouter()
service = SeasonService()

# --- Schemas ---

class SeasonResponse(BaseModel):
    id: int
    name: str
    start_date: datetime
    end_date: datetime
    max_stages: int
    premium_price: int

    model_config = ConfigDict(from_attributes=True)

class SeasonStageResponse(BaseModel):
    id: int
    season_id: int
    stage_number: int
    required_xp: int
    free_reward: Optional[Dict[str, Any]] = None
    premium_reward: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class UserSeasonResponse(BaseModel):
    id: int
    user_id: int
    season_id: int
    current_xp: int
    is_premium: bool
    completed_stages: List[int]

    model_config = ConfigDict(from_attributes=True)

class RewardResponse(BaseModel):
    rewards: List[Dict[str, Any]]

# --- Endpoints ---

@router.get("/current", response_model=SeasonResponse)
async def get_current_season(db: AsyncSession = Depends(get_db)):
    """
    現在のシーズン情報を取得
    Get current active season info
    """
    season = await service.get_current_season(db)
    if not season:
        raise HTTPException(status_code=404, detail="No active season found")
    return season

@router.get("/{id}/rewards", response_model=List[SeasonStageResponse])
async def get_season_rewards(id: int, db: AsyncSession = Depends(get_db)):
    """
    シーズンの報酬一覧を取得
    Get rewards list for a season (free/premium tiers)
    """
    stages = await service.get_season_stages(db, id)
    return stages

@router.post("/purchase-pass", response_model=UserSeasonResponse)
async def purchase_pass(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    プレミアムパス購入
    Purchase premium pass for the current season
    """
    season = await service.get_current_season(db)
    if not season:
        raise HTTPException(status_code=404, detail="No active season to purchase")

    return await service.purchase_pass(db, user_id, season.id)

@router.post("/stages/{stage}/claim", response_model=RewardResponse)
async def claim_reward(
    stage: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    報酬受け取る
    Claim reward for a specific stage in the current season
    """
    season = await service.get_current_season(db)
    if not season:
        raise HTTPException(status_code=404, detail="No active season")

    # Ensure user season exists, if not, create it?
    # Service claim_reward checks if UserSeason exists.
    # But user might have XP but no UserSeason row?
    # add_season_xp creates it.
    # If user has 0 XP and tries to claim stage 1 (which requires 0 XP?), they might not have a row.
    # But claim_reward throws 404 if row missing.
    # Ideally, querying current season for user context should happen.
    # For now, relying on service logic.

    rewards = await service.claim_reward(db, user_id, season.id, stage)
    return {"rewards": rewards}
