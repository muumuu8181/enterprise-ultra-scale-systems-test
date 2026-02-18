from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.v1.parcels import router as parcels_router
from src.core.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

app.include_router(parcels_router, prefix="/api/v1")
