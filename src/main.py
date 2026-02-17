from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.core.database import engine, Base
from src.api.v1.vehicles import router as vehicles_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup on shutdown (if needed)

app = FastAPI(title="Rental Car Service", lifespan=lifespan)

app.include_router(vehicles_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Rental Car Service API"}
