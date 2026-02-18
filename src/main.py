from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.core.database import engine, Base
from src.api.v1 import serving

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Close engine
    await engine.dispose()

app = FastAPI(
    title="ML Ops Platform",
    description="Enterprise Ultra Scale ML Ops Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(serving.router, prefix="/api/v1/serving", tags=["Serving"])

@app.get("/")
async def root():
    return {"message": "ML Ops Platform is running"}
