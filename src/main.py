from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.v1.assignments import router as assignments_router
from src.core.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown

app = FastAPI(title="Virtual Classroom Platform", lifespan=lifespan)

app.include_router(assignments_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to the Virtual Classroom Platform"}
