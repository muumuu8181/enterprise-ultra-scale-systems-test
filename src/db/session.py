from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

DATABASE_URL = "sqlite+aiosqlite:///./risk_platform.db"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
