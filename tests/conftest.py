import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from src.core.database import Base, get_db
# Import all models to ensure metadata is populated
from src.models import Customer, Account, Transaction, TransactionEntry, AuditLog
from src.main import app
from src.core.config import get_settings
from httpx import AsyncClient, ASGITransport
import asyncio

# Override settings for testing
settings = get_settings()
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def db_engine():
    # Create an async engine for SQLite with StaticPool to share in-memory DB
    # Enable SERIALIZABLE isolation to mimic strict locking behavior
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        isolation_level="SERIALIZABLE",
        echo=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    # Factory for sessions
    TestingSessionLocal = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )

    async with TestingSessionLocal() as session:
        yield session
        # No rollback here because we might commit in tests.
        # Since DB is recreated per test function (db_engine scope=function), it's clean.

@pytest_asyncio.fixture(scope="function")
async def client(db_engine):
    # Create a new session factory for the client override
    TestingSessionLocal = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )

    # Override get_db to create NEW session per request
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # Create AsyncClient
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
