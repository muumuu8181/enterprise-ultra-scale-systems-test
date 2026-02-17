import pytest_asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
import fakeredis.aioredis
from typing import AsyncGenerator

from src.main import app
from src.database import get_db
from src.models.base import Base
from src.deps import get_redis

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        # Clean up tables after test?
        # Since scope is function and using :memory: DB, it persists per connection/engine unless dropped.
        # But using StaticPool means the DB persists across connections in same process.
        # So we should drop all tables after yield or before create.
        # Actually, best practice for isolation: drop all at end.
        pass

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def redis_client() -> AsyncGenerator[fakeredis.aioredis.FakeRedis, None]:
    server = fakeredis.FakeServer()
    # fakeredis.aioredis.FakeRedis(server=server, decode_responses=True)
    # Note: fakeredis 2.0+ supports async via aioredis module (deprecated) or standard redis-py interface?
    # redis-py 4.2+ integrated async. fakeredis mirrors it.
    # checking fakeredis usage:
    # r = fakeredis.FakeAsyncRedis()
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.flushall()
    await r.close()

@pytest_asyncio.fixture(scope="function")
async def client(db_session, redis_client) -> AsyncGenerator[AsyncClient, None]:
    # Override dependencies
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        yield redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
