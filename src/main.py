from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database import engine, Base
from src.api.v1.scouting import router as scouting_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup on shutdown

app = FastAPI(title="Sports Analytics Platform", version="1.0.0", lifespan=lifespan)

app.include_router(scouting_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Sports Analytics Platform API"}
