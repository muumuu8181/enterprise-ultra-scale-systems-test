from fastapi import FastAPI
from src.api.v1.monetization import router as monetization_router

app = FastAPI()

app.include_router(monetization_router, prefix="/api/v1")
