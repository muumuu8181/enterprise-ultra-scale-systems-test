from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from src.database import get_db
from src.models.leaderboard import GlobalLeaderboard, LeaderboardEntry, PlayerStats
from src.services.scoring import submit_score, get_percentile

router = APIRouter()

class ScoreSubmission(BaseModel):
    player_id: str
    game_id: str
    score: float
    metadata: Optional[Dict[str, Any]] = None

class LeaderboardEntryResponse(BaseModel):
    player_id: str
    score: float
    rank: int
    rank_change: int
    metadata: Optional[Dict[str, Any]] = Field(None, alias="meta_data") # Map meta_data from DB to metadata in response

    class Config:
        from_attributes = True

class PlayerStatsResponse(BaseModel):
    player_id: str
    game_id: str
    total_playtime_hrs: float
    highest_score: float
    matches_won: int
    matches_lost: int
    percentile: float

    class Config:
        from_attributes = True

@router.get("/leaderboards/{game_id}/global", response_model=List[LeaderboardEntryResponse])
async def get_global_leaderboard(
    game_id: str,
    period: str = Query("alltime"),
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    # Find leaderboard for game and period
    # Note: Currently only "alltime" is fully implemented in service, but we query by period
    # If period is not found, return empty list or fallback
    query = select(GlobalLeaderboard).where(GlobalLeaderboard.game_id == game_id, GlobalLeaderboard.period == period)
    result = await db.execute(query)
    leaderboard = result.scalars().first()

    if not leaderboard:
        return []

    entries_query = select(LeaderboardEntry).where(LeaderboardEntry.leaderboard_id == leaderboard.id).order_by(desc(LeaderboardEntry.score)).limit(limit)
    result = await db.execute(entries_query)
    entries = result.scalars().all()

    # Map 'meta_data' to 'metadata' via Pydantic alias
    return entries

@router.get("/leaderboards/{game_id}/friends/{player_id}", response_model=List[LeaderboardEntryResponse])
async def get_friends_leaderboard(
    game_id: str,
    player_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Mock implementation as Friend model is not defined
    return []

@router.post("/scores/submit")
async def submit_player_score(
    submission: ScoreSubmission,
    db: AsyncSession = Depends(get_db)
):
    await submit_score(db, submission.player_id, submission.game_id, submission.score, submission.metadata)
    return {"status": "success"}

@router.get("/players/{id}/stats", response_model=PlayerStatsResponse)
async def get_player_stats(
    id: str,
    game_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    stats_query = select(PlayerStats).where(PlayerStats.player_id == id, PlayerStats.game_id == game_id)
    result = await db.execute(stats_query)
    stats = result.scalars().first()

    if not stats:
        raise HTTPException(status_code=404, detail="Player stats not found")

    percentile = await get_percentile(db, id, game_id)

    # Combine stats and percentile
    return PlayerStatsResponse(
        player_id=stats.player_id,
        game_id=stats.game_id,
        total_playtime_hrs=stats.total_playtime_hrs,
        highest_score=stats.highest_score,
        matches_won=stats.matches_won,
        matches_lost=stats.matches_lost,
        percentile=percentile
    )

@router.get("/players/{id}/achievements/progress")
async def get_achievements(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    # Mock implementation
    return {"achievements": [], "progress": 0.0}
