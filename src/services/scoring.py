from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from src.models.leaderboard import GlobalLeaderboard, LeaderboardEntry, PlayerStats
from datetime import datetime
from typing import Dict, Any, Optional

async def submit_score(db: AsyncSession, player_id: str, game_id: str, score: float, metadata: Optional[Dict[str, Any]] = None):
    # 1. Update PlayerStats
    result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id, PlayerStats.game_id == game_id))
    stats = result.scalars().first()

    if not stats:
        stats = PlayerStats(player_id=player_id, game_id=game_id, highest_score=score, matches_won=0, matches_lost=0, total_playtime_hrs=0)
        db.add(stats)
    else:
        if score > stats.highest_score:
            stats.highest_score = score

    # 2. Add to Global Leaderboard (All-time)
    # Find or create leaderboard
    result = await db.execute(select(GlobalLeaderboard).where(GlobalLeaderboard.game_id == game_id, GlobalLeaderboard.period == "alltime"))
    leaderboard = result.scalars().first()

    if not leaderboard:
        leaderboard = GlobalLeaderboard(game_id=game_id, period="alltime", last_updated=datetime.utcnow())
        db.add(leaderboard)
        await db.flush() # flush to get ID

    # Create or update entry
    result = await db.execute(select(LeaderboardEntry).where(LeaderboardEntry.leaderboard_id == leaderboard.id, LeaderboardEntry.player_id == player_id))
    entry = result.scalars().first()

    if entry:
        if score > entry.score:
            entry.score = score
            entry.meta_data = metadata
            entry.last_updated = datetime.utcnow()
    else:
        entry = LeaderboardEntry(leaderboard_id=leaderboard.id, player_id=player_id, score=score, rank=0, rank_change=0, meta_data=metadata)
        db.add(entry)

    await db.commit()
    await db.refresh(stats)
    return stats

async def recalculate_rankings(db: AsyncSession, leaderboard_id: int):
    # Fetch all entries sorted by score desc
    result = await db.execute(select(LeaderboardEntry).where(LeaderboardEntry.leaderboard_id == leaderboard_id).order_by(desc(LeaderboardEntry.score)))
    entries = result.scalars().all()

    current_rank = 1
    for entry in entries:
        old_rank = entry.rank
        entry.rank = current_rank
        if old_rank != 0:
            entry.rank_change = old_rank - current_rank
        else:
            entry.rank_change = 0 # New entry
        current_rank += 1

    # Update last_updated on leaderboard
    result = await db.execute(select(GlobalLeaderboard).where(GlobalLeaderboard.id == leaderboard_id))
    leaderboard = result.scalars().first()
    if leaderboard:
        leaderboard.last_updated = datetime.utcnow()

    await db.commit()

async def get_percentile(db: AsyncSession, player_id: str, game_id: str) -> float:
    # Get total players
    # Assuming alltime leaderboard for percentile
    result = await db.execute(select(GlobalLeaderboard).where(GlobalLeaderboard.game_id == game_id, GlobalLeaderboard.period == "alltime"))
    leaderboard = result.scalars().first()

    if not leaderboard:
        return 0.0

    total_count = await db.scalar(select(func.count(LeaderboardEntry.id)).where(LeaderboardEntry.leaderboard_id == leaderboard.id))

    if total_count == 0:
        return 0.0

    # Get player rank
    result = await db.execute(select(LeaderboardEntry).where(LeaderboardEntry.leaderboard_id == leaderboard.id, LeaderboardEntry.player_id == player_id))
    entry = result.scalars().first()

    if not entry or entry.rank == 0:
        return 0.0

    # Percentile = (Total - Rank) / Total * 100
    # Top player (Rank 1) should be near 100%? Or 100th percentile?
    # Usually percentile is "percentage of people below you".
    # (Total - Rank) / Total.
    # E.g. 100 players. Rank 1. (100 - 1) / 100 = 0.99 -> 99th percentile.
    # Rank 100. (100 - 100) / 100 = 0 -> 0th percentile.

    percentile = (total_count - entry.rank) / total_count * 100.0
    return percentile
