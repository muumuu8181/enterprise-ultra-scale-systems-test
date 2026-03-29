from fastapi import FastAPI
from src.api.v1 import prison

app = FastAPI(title="Prison Management Platform")

app.include_router(prison.router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}
