from fastapi import FastAPI
from src.api.v1.fire_ops import router as fire_ops_router

app = FastAPI(title="Fire Department Operations Platform")

app.include_router(fire_ops_router)
