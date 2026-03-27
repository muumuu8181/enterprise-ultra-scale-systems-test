from fastapi import FastAPI
from src.api.v1 import vineyard
from src.database import engine, Base
from src.models import vineyard_models # This ensures models are imported and registered with Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vineyard Management Platform")

app.include_router(vineyard.router, prefix="/api/v1", tags=["vineyard"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Vineyard Management Platform"}
