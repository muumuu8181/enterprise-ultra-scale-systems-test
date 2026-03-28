from fastapi import FastAPI
from src.api.v1.bee import router as bee_router
from src.database import engine, Base
import contextlib

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (for demo purposes)
    # In production, use Alembic for migrations
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup (if needed)

app = FastAPI(title="Bee Colony Monitoring Platform", lifespan=lifespan)

app.include_router(bee_router, prefix="/api/v1", tags=["Bee Monitoring"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Bee Colony Monitoring Platform API"}
