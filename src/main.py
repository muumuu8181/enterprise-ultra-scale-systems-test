from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from redis import asyncio as aioredis
from src.core.config import settings
from src.routers import gacha, events, shop, rankings, admin

redis_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_pool
    # Initialize Redis connection pool
    redis_pool = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    yield
    # Close Redis connection pool
    if redis_pool:
        await redis_pool.close()

app = FastAPI(title="Game Platform API", lifespan=lifespan)

# Register Routers
app.include_router(gacha.router)
app.include_router(events.router)
app.include_router(shop.router)
app.include_router(rankings.router)
app.include_router(admin.router)

@app.websocket("/ws/rankings")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # In a real app, this would subscribe to Redis pub/sub for ranking updates
            await websocket.send_text(f"Current rankings update requested: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
