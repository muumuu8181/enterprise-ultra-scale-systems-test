from fastapi import FastAPI
from .api.v1 import sessions

app = FastAPI(title="Gaming Cloud Platform", version="1.0.0")

app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
