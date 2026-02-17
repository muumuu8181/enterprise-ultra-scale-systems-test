from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.v1 import waste
from src.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Nuclear Waste Management Platform", lifespan=lifespan)

app.include_router(waste.router, prefix="/api/v1")
