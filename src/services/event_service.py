from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.event import EventPoint, LiveEvent
from src.database import settings

class EventService:
    @staticmethod
    def get_redis_key(event_id: int) -> str:
        return f"event:{event_id}:ranking"

    @classmethod
    async def add_points(cls, db: AsyncSession, redis: Redis, user_id: int, event_id: int, points: int):
        # Update DB (could be async task but doing synchronous for consistency)
        # Check if record exists
        # In real world, use UPSERT
        from sqlalchemy.dialects.postgresql import insert
        stmt = insert(EventPoint).values(user_id=user_id, event_id=event_id, point=points)
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id', 'event_id'],
            set_={EventPoint.point: EventPoint.point + points, EventPoint.updated_at: stmt.excluded.updated_at}
        )
        await db.execute(stmt)

        # Update Redis Sorted Set
        key = cls.get_redis_key(event_id)
        await redis.zincrby(key, points, str(user_id))

    @classmethod
    async def get_ranking(cls, redis: Redis, event_id: int, start: int = 0, end: int = 9):
        key = cls.get_redis_key(event_id)
        # Returns list of (member, score)
        return await redis.zrevrange(key, start, end, withscores=True)
