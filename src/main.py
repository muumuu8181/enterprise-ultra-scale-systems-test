from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.v1.reactors import router as reactor_router
from src.db.session import engine
from src.models.base import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown

app = FastAPI(title="Nuclear Plant Monitoring", lifespan=lifespan)

app.include_router(reactor_router, prefix="/api/v1", tags=["reactors"])

@app.get("/")
async def root():
    return {"message": "Nuclear Plant Monitoring System"}
