from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.v1.warehouse import router as warehouse_router
from src.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Warehouse Robotics Platform", lifespan=lifespan)

app.include_router(warehouse_router, prefix="/api/v1", tags=["warehouse"])

@app.get("/")
async def root():
    return {"message": "Warehouse Robotics Platform is running"}
