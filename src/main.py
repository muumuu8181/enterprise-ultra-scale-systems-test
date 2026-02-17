from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.v1.settlement import router as settlement_router
from src.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Auction Marketplace Platform", lifespan=lifespan)

app.include_router(settlement_router, prefix="/api/v1", tags=["settlement"])

@app.get("/")
async def root():
    return {"message": "Auction Marketplace Platform is running"}
