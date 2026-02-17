from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database import engine, Base
from src.api.v1 import vet

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Veterinary Clinic Platform", lifespan=lifespan)

app.include_router(vet.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Veterinary Clinic Platform API"}
