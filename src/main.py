from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database import engine, Base
from src.api.v1.customs import router as customs_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (for prototype/test purpose)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Customs Clearance Platform", lifespan=lifespan)

app.include_router(customs_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
