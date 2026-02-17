from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.v1.operations import router as operations_router
from src.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables (dev)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown

app = FastAPI(title="Passenger Rail Platform", version="1.0.0", lifespan=lifespan)

app.include_router(operations_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Passenger Rail Platform API"}
