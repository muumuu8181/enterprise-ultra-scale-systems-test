from fastapi import FastAPI
from src.api.v1.automl import router as automl_router
from src.database import engine
from src.models.ml_models import Base
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown

app = FastAPI(title="AI/ML Integration Platform", lifespan=lifespan)

app.include_router(automl_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to AI/ML Integration Platform"}
