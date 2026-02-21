from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database import engine, Base
from src.api.v1.theme_park import router as theme_park_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables (for dev purposes)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="Theme Park Management Platform",
    description="API for managing attractions, tickets, and wait times.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(theme_park_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Theme Park Management Platform"}
