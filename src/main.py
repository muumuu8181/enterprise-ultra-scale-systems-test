from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.services.model_registry import init_models
from src.api.v1.models import router as models_router
from src.api.v1.annotations import router as annotations_router
import src.models.annotation_models # Ensure registration

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションのライフサイクル管理
    起動時にデータベーステーブルを作成します。
    """
    # Ensure all models are imported so Base.metadata knows about them
    # src.models.ml_models is imported by model_registry
    # src.models.annotation_models is imported above
    await init_models()
    yield

app = FastAPI(
    title="AI/ML Integration Platform",
    description="Enterprise Ultra Scale Systems Test - AI/ML Integration",
    version="1.0.0",
    lifespan=lifespan
)

# Include Routers
app.include_router(models_router, prefix="/api/v1")
app.include_router(annotations_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "AI/ML Integration Platform API"}
