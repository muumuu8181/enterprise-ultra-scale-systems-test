from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.v1.contracts import router as contracts_router
from src.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Legal Contract Management Platform", lifespan=lifespan)

app.include_router(contracts_router, prefix="/api/v1", tags=["contracts"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
