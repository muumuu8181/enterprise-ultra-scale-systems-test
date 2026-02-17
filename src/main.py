from fastapi import FastAPI
from src.api.v1 import trials
from src.db.session import engine
from src.db.base import Base

app = FastAPI(title="Drug Discovery Platform")

app.include_router(trials.router, prefix="/api/v1", tags=["trials"])

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "Drug Discovery Platform API"}
