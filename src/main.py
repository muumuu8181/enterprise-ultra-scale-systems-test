from fastapi import FastAPI
from src.api.v1.water import router as water_router
from src.database import engine, Base

app = FastAPI(title="Water Treatment Monitoring Platform")

app.include_router(water_router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Create tables for demo purposes
        import src.models.water_models
        await conn.run_sync(Base.metadata.create_all)
