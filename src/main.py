from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.database import engine, Base
from src.api.v1.port import router as port_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(port_router, prefix="/api/v1", tags=["port"])
