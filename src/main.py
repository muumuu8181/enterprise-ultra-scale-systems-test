from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.v1.batches import router as batches_router
from src.core.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(batches_router, prefix="/api/v1")
