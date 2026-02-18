from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.v1.secondary import router as secondary_router
from src.core.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown

app = FastAPI(title="Concert Ticketing Platform", lifespan=lifespan)

app.include_router(secondary_router, prefix="/api/v1", tags=["secondary"])
