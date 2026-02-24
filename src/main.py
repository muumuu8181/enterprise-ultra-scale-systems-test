from fastapi import FastAPI
from src.api.v1 import patents
from src.database import engine, Base

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Error creating tables: {e}")
    yield

app = FastAPI(title="Patent Management Platform", lifespan=lifespan)

app.include_router(patents.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Patent Management Platform"}
