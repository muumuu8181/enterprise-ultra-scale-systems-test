import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI
from contextlib import asynccontextmanager
import fakeredis.aioredis
from unittest.mock import patch

from src.database import Base, get_db
from src.models import Customer
from src.core.security import get_password_hash
from src.api.v1.auth import router as auth_router
from src.middleware.auth_middleware import JWTAuthMiddleware

# Setup Test App
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

def create_app():
    app = FastAPI(lifespan=lifespan)
    # Include router
    app.include_router(auth_router, prefix="/api/v1")
    # Add middleware
    app.add_middleware(JWTAuthMiddleware, exclude_paths=["/api/v1/auth/login", "/api/v1/auth/refresh", "/docs", "/openapi.json"])
    return app

app = create_app()

# Setup Test Database (In-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

@pytest_asyncio.fixture
async def db_session():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(db_session):
    # Override get_db dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create Mock Redis
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    # We patch strictly for the context of the client
    # But patching 'src.core.security.redis_client' globally is tricky with async fixtures.
    # It's better to rely on the fact that `security.py` imports `redis_client`.
    # We can overwrite the variable.
    import src.core.security as security
    old_client = security.redis_client
    security.redis_client = fake_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    security.redis_client = old_client
    await fake_redis.close()

@pytest_asyncio.fixture
async def test_customer(db_session):
    hashed_pin = get_password_hash("1234")
    customer = Customer(id="user1", pin_hash=hashed_pin, is_active=True)
    db_session.add(customer)
    await db_session.commit()
    return customer
