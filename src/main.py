from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.db.session import engine
from src.db.base import Base
from src.models import audit_models
from src.models import treasury_models
from src.api.v1 import contracts
from src.api.v1 import treasury

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(title="Smart Contract Audit System", lifespan=lifespan)

app.include_router(contracts.router, prefix="/api/v1")
app.include_router(treasury.router, prefix="/api/v1", tags=["Treasury"])
