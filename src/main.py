from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database import engine, Base
from src.api.v1.archive import router as archive_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Archive Preservation Platform", lifespan=lifespan)

app.include_router(archive_router, prefix="/api/v1", tags=["Archive"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Archive Preservation Platform"}
