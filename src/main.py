from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.v1.gallery import router as gallery_router
from src.database import Base, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Art Gallery Management Platform",
    lifespan=lifespan
)

app.include_router(gallery_router, prefix="/api/v1", tags=["gallery"])
