from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database import engine, Base
from src.api.v1.processing import router as processing_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup (if any)

app = FastAPI(title="Archive Preservation Platform", version="1.0.0", lifespan=lifespan)

app.include_router(processing_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Archive Preservation Platform API"}
