from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database import engine, Base
from src.api.v1.events import router as events_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # In production, use Alembic. For dev/demo, create tables.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Event Management Platform", version="1.0.0", lifespan=lifespan)

app.include_router(events_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Event Management Platform API"}
