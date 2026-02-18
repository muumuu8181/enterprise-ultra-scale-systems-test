import redis.asyncio as redis
import os

# Create a global Redis client (connection pool)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Connection pool is managed by redis-py internally when using from_url
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def get_redis():
    """
    FastAPI dependency for Redis client (if needed)
    """
    return redis_client

async def close_redis():
    """
    Close Redis connection pool
    """
    await redis_client.close()
