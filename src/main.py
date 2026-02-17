from fastapi import FastAPI
from src.api.v1.court import router as court_router

app = FastAPI(title="Court Case Management Platform")

app.include_router(court_router, prefix="/api/v1")
