from typing import Annotated
from fastapi import Depends, Header, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db, settings

async def get_redis() -> Redis:
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.close()

async def get_current_user_id(x_user_id: Annotated[int, Header()] = 1) -> int:
    # Simplified auth
    return x_user_id
