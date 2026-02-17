from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.v1.sensors import router as sensor_router
from src.api.v1.traffic import router as traffic_router
from src.api.v1.emergency import router as emergency_router
from src.api.v1.water import router as water_router
from src.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時の処理: テーブル作成 (開発用)
    # 本番環境ではAlembicなどのマイグレーションツールを使用すべきです
    async with engine.begin() as conn:
        # PostGIS拡張が有効なDBである必要があります
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 終了時の処理

app = FastAPI(title="Smart City Platform", version="1.0.0", lifespan=lifespan)

app.include_router(sensor_router, prefix="/api/v1")
app.include_router(traffic_router, prefix="/api/v1")
app.include_router(emergency_router, prefix="/api/v1")
app.include_router(water_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Smart City Platform API"}
