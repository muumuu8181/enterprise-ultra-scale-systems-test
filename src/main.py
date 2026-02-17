from fastapi import FastAPI
from src.api.v1.training_jobs import router as training_jobs_router
from src.api.v1.feature_store import router as feature_store_router
from src.api.v1.model_serving import router as model_serving_router

app = FastAPI(
    title="AI/ML Integration Platform",
    description="Enterprise-grade AI/ML infrastructure API",
    version="1.0.0"
)

# Include routers
app.include_router(training_jobs_router, prefix="/training", tags=["Training Jobs"])
app.include_router(feature_store_router, prefix="/features", tags=["Feature Store"])
app.include_router(model_serving_router)

@app.get("/")
async def root():
    return {"message": "Welcome to AI/ML Integration Platform"}
