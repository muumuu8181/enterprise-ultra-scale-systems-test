from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.core.database import engine, Base
from src.api.v1.properties import router as properties_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Dispose engine
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(properties_router, prefix="/api/v1")
