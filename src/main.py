from fastapi import FastAPI
from src.api.v1.cruise import router as cruise_router

app = FastAPI(title="Cruise Ship Operations Platform")

app.include_router(cruise_router, prefix="/api/v1", tags=["cruise"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Cruise Ship Operations Platform API"}
