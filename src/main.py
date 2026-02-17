from fastapi import FastAPI
from src.api.v1.custody import router as custody_router
from src.database import engine, Base

app = FastAPI(title="Cryptocurrency Custody Platform")

app.include_router(custody_router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
async def health():
    return {"status": "ok"}
