from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
import os

# Read from environment, default to in-memory SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
