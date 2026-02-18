from fastapi import FastAPI
from src.api.v1.properties import router as properties_router

app = FastAPI()

app.include_router(properties_router)
