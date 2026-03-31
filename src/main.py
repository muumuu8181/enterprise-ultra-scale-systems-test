from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.v1.experience import router as experience_router
from src.database import engine, Base
import src.models.employee_models

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Employee Experience Platform", lifespan=lifespan)

app.include_router(experience_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Employee Experience Platform"}
