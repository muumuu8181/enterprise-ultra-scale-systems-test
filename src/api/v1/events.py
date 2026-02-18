from typing import List, Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from src.database import get_db
from src.deps import get_redis, get_current_user_id
from src.models.event import LiveEvent
from src.schemas import EventResponse, EventPlayRequest, EventRankingItem
from src.services.event_service import EventService

router = APIRouter()

@router.get("/active", response_model=List[EventResponse])
async def get_active_events(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    now = datetime.utcnow()
    # Simple query
    stmt = select(LiveEvent).where(LiveEvent.start_time <= now).where(LiveEvent.end_time >= now)
    result = await db.execute(stmt)
    events = result.scalars().all()
    return events

@router.post("/{event_id}/play")
async def play_event(
    event_id: int,
    request: EventPlayRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    event = await db.get(LiveEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await EventService.add_points(db, redis, user_id, event_id, request.points)
    return {"status": "ok", "points_added": request.points}

@router.get("/{event_id}/ranking", response_model=List[EventRankingItem])
async def get_event_ranking(
    event_id: int,
    redis: Annotated[Redis, Depends(get_redis)],
    start: int = 0,
    end: int = 9,
):
    ranking_data = await EventService.get_ranking(redis, event_id, start, end)
    # data is list of (member, score)
    result = []
    current_rank = start + 1
    for member, score in ranking_data:
        result.append(EventRankingItem(
            user_id=int(member),
            score=int(score),
            rank=current_rank
        ))
        current_rank += 1
    return result
