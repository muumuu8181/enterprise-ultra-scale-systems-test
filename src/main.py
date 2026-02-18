from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.v1.investigation import router as investigation_router
from src.core.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Clean up if needed

app = FastAPI(title="Fraud Detection Platform", lifespan=lifespan)

app.include_router(investigation_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Fraud Detection Platform API"}
