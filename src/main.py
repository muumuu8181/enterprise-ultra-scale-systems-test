from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database import engine, Base
from src.api.v1.blood_bank import router as blood_bank_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # In production, use Alembic. For this demo/test, create tables on startup.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Blood Bank Management Platform", lifespan=lifespan)

app.include_router(blood_bank_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Blood Bank Management Platform API"}
