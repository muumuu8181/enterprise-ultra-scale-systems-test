from fastapi import FastAPI
from src.api.v1.carbon import router as carbon_router
from src.database import engine
from src.models.base import Base

app = FastAPI()

app.include_router(carbon_router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
