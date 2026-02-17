from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.v1 import recycling
from src.database import engine, Base
from src.models import recycling_models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # Log error but allow app to start, helpful for tests where DB might be mocked/missing
        print(f"Warning: Database tables could not be created. Error: {e}")
    yield

app = FastAPI(title="Recycling Management Platform", lifespan=lifespan)

app.include_router(recycling.router, prefix="/api/v1/recycling", tags=["recycling"])
