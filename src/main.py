from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from src.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import models here to ensure they are registered with Base metadata
    from src.models import museum_models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Museum Collection Platform", lifespan=lifespan)

from src.api.v1 import museum
app.include_router(museum.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to the Museum Collection Platform"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
