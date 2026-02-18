from fastapi import FastAPI
from src.core.config import settings
from src.db.session import engine
from contextlib import asynccontextmanager
from src.api.v1 import inventory

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to DB
    yield
    await engine.dispose()

app = FastAPI(title="Manufacturing MES API", lifespan=lifespan)
app.include_router(inventory.router, prefix="/api/v1")
