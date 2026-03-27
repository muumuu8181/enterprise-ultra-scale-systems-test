from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.v1.freight import router as freight_router
from src.database import Base, engine
from src.models import freight_models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # In production, this might be critical, but for dev/test in isolation it's okay to fail
        print(f"Warning: Could not connect to database to create tables: {e}")
    yield

app = FastAPI(title="Freight Forwarding Platform", lifespan=lifespan)

app.include_router(freight_router, prefix="/api/v1/freight", tags=["freight"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
