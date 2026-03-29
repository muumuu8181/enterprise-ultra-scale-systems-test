from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.v1.pricing import router as pricing_router
from src.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Retail Price Optimization Platform", lifespan=lifespan)

app.include_router(pricing_router, prefix="/api/v1", tags=["pricing"])
