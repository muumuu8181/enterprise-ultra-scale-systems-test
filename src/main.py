from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database import engine, Base
from src.api.v1 import pharmacy

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Dispose engine
    await engine.dispose()

app = FastAPI(
    title="Pharmacy Management Platform",
    lifespan=lifespan
)

app.include_router(pharmacy.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Pharmacy Management Platform API"}
