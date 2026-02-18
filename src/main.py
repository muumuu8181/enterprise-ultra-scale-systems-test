from fastapi import FastAPI
from src.api.v1.policies import router as policies_router

app = FastAPI(title="Insurance Platform")

app.include_router(policies_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Insurance Platform API"}
