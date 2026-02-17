from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.v1.toll import router as toll_router
from src.api.v1.v2x_messages import router as v2x_router
from src.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB
    await init_db()
    yield
    # Shutdown

app = FastAPI(title="V2X Autonomous Driving & Toll System", lifespan=lifespan)

app.include_router(toll_router)
app.include_router(v2x_router)

@app.get("/")
async def root():
    return {"message": "V2X System Operational"}
