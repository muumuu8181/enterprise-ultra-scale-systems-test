from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.database import engine
from src.api.v1 import gacha, events, purchase, story

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(gacha.router, prefix="/gacha", tags=["Gacha"])
app.include_router(events.router, prefix="/events", tags=["Events"])
app.include_router(purchase.router, prefix="/purchase", tags=["Purchase"])
app.include_router(story.router, prefix="/story", tags=["Story"])

@app.get("/")
async def root():
    return {"message": "Game Gacha System API"}
