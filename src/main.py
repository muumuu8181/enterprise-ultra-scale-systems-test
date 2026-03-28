from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.v1.training import router_training, router_policies, router_curriculum
from src.database import engine, Base
import src.models.rl_models # Register models

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Robotics Simulation Platform", lifespan=lifespan)

app.include_router(router_training, prefix="/api/v1")
app.include_router(router_policies, prefix="/api/v1")
app.include_router(router_curriculum, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Robotics Simulation Platform is running"}
