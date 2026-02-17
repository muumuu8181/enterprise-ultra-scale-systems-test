from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.core.config import settings
from src.api.v1.quantum import router as quantum_router
from src.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

app.include_router(quantum_router, prefix=f"{settings.API_V1_STR}", tags=["quantum"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
