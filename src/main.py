from fastapi import FastAPI
from src.api.v1.optimization import router as optimization_router

app = FastAPI(title="Cloud Cost Optimization Platform")

app.include_router(optimization_router, prefix="/api/v1")
