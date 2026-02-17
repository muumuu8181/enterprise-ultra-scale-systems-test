from fastapi import FastAPI
from src.api.v1.drivers import router as drivers_router
from src.core.config import settings

app = FastAPI(title="Food Delivery Platform")

app.include_router(drivers_router, prefix="/api/v1", tags=["drivers"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
