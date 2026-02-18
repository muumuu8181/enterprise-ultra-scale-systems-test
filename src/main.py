from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.database import Base, engine
from src.api.v1 import posts

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Social Media Platform", lifespan=lifespan)

app.include_router(posts.router, prefix="/api/v1", tags=["posts"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Social Media Platform"}
