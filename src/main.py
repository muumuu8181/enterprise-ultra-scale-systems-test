from fastapi import FastAPI
from src.api.v1.fleet import router as fleet_router

app = FastAPI(title="Fleet Management API")

app.include_router(fleet_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Fleet Management API"}
