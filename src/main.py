from fastapi import FastAPI
from src.api.v1 import jobs, clusters

app = FastAPI(title="Scientific Computing Platform")

app.include_router(jobs.router, prefix="/api/v1")
app.include_router(clusters.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to the Scientific Computing Platform"}
