import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from src.core.database import Base, get_db
from src.main import app

# テスト用インメモリSQLiteデータベース
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="session")
async def engine():
    # インメモリSQLiteエンジンを作成 (StaticPoolを使用して接続を維持)
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    # テーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # セッション作成
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session

    # テーブル削除 (クリーンアップ)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    # get_db依存関係をオーバーライド
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # 非同期クライアントを作成
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
