import os
from typing import Optional
from redis.asyncio import Redis, from_url as redis_from_url

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class RedisClient:
    _instance: Optional[Redis] = None

    @classmethod
    def get_client(cls) -> Redis:
        if cls._instance is None:
            cls._instance = redis_from_url(REDIS_URL, decode_responses=True)
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.close()
            cls._instance = None

def get_redis_client() -> Redis:
    """
    グローバルRedisクライアントを取得します。
    """
    return RedisClient.get_client()
