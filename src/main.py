from fastapi import FastAPI
from src.api.v1.agriculture import router as agriculture_router
from src.database import engine, Base
import contextlib

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(agriculture_router, prefix="/api/v1", tags=["agriculture"])

@app.get("/")
async def root():
    return {"message": "Smart Agriculture IoT Platform API"}
