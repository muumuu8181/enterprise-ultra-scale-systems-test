from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/smartcity")
TIMESCALE_URL = os.getenv("TIMESCALE_URL", "postgresql+asyncpg://user:password@localhost:5433/timescale")

# PostGIS Engine
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# TimescaleDB Engine
timescale_engine = create_async_engine(TIMESCALE_URL, echo=True)
AsyncTimescaleSessionLocal = sessionmaker(timescale_engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    """Dependency for PostGIS session"""
    async with AsyncSessionLocal() as session:
        yield session

async def get_timescale_db():
    """Dependency for TimescaleDB session"""
    async with AsyncTimescaleSessionLocal() as session:
        yield session
