from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.v1.rare_earth import router as rare_earth_router
from src.core.config import settings
from src.core.database import Base, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # In a production environment, use Alembic migrations instead of create_all
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(rare_earth_router, prefix="/api/v1", tags=["rare_earth"])

@app.get("/")
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}
