"""
デジタルツインAPI
スマートシティのデジタルツイン機能を提供するAPIエンドポイント
"""
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from ...services.digital_twin import DigitalTwin
from ...database import get_db, get_timescale_db
import asyncio

# アプリケーションの定義
app = FastAPI(
    title="Smart City Digital Twin API",
    description="都市インフラのデジタルツイン管理API",
    version="1.0.0"
)

@app.get("/digital-twin/state", summary="都市全体の現在状態を取得")
async def get_state(db: AsyncSession = Depends(get_db), timescale_db: AsyncSession = Depends(get_timescale_db)):
    """
    都市全体の現在状態をGeoJSON形式で返します。
    """
    service = DigitalTwin(db, timescale_db)
    return await service.visualize_state()

@app.get("/digital-twin/metrics", summary="集計メトリクスを取得")
async def get_metrics(db: AsyncSession = Depends(get_db), timescale_db: AsyncSession = Depends(get_timescale_db)):
    """
    都市全体の集計メトリクス（AQI、渋滞率、エネルギー消費など）を返します。
    """
    service = DigitalTwin(db, timescale_db)
    return await service.calculate_city_metrics()

@app.get("/digital-twin/anomalies", summary="検知された異常一覧を取得")
async def get_anomalies(db: AsyncSession = Depends(get_db), timescale_db: AsyncSession = Depends(get_timescale_db)):
    """
    統計的予測に基づいて検知された異常（外れ値）の一覧を返します。
    """
    service = DigitalTwin(db, timescale_db)
    return await service.predict_anomaly()

@app.websocket("/ws/digital-twin")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db), timescale_db: AsyncSession = Depends(get_timescale_db)):
    """
    リアルタイムストリーム用WebSocketエンドポイント
    都市の状態を定期的にプッシュ通知します。
    """
    await websocket.accept()
    service = DigitalTwin(db, timescale_db)
    try:
        while True:
            # リアルタイムでデータを送信
            # 本番環境ではMQTTサブスクリプションなどからのプッシュが望ましいが、
            # ここではポーリングで実装
            state = await service.visualize_state()
            await websocket.send_json(state)

            # 5秒ごとに更新
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        # 接続切断時の処理
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()
