from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.v1.devices import router as devices_router
from src.db.session import engine
from src.models.wearable_models import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(title="Health Wearable Platform", lifespan=lifespan)

app.include_router(devices_router)
