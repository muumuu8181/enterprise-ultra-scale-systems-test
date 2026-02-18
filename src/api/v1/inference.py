from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import asyncio

from src.models.ml_models import get_db
from src.services.inference_engine import InferenceEngine

router = APIRouter(prefix="/inference", tags=["inference"])

# --- Schemas ---

class PredictionRequest(BaseModel):
    data: List[Any] = Field(..., description="入力データリスト")

class BatchPredictionRequest(BaseModel):
    data: List[List[Any]] = Field(..., description="バッチ入力データリスト (最大1000件)", max_length=1000)

class PredictionResponse(BaseModel):
    predictions: List[Any]

class BatchPredictionResponse(BaseModel):
    results: List[Dict[str, Any]]

class StatsResponse(BaseModel):
    count: int
    p50: float
    p95: float
    p99: float
    throughput: float

class RouteResponse(BaseModel):
    model_id: int

# --- Endpoints ---

@router.post("/{model_id}/predict", response_model=PredictionResponse, summary="予測実行", description="モデルを使用して予測を実行します（タイムアウト30秒）。")
async def predict(model_id: int, request: PredictionRequest, db: AsyncSession = Depends(get_db)):
    engine = InferenceEngine(db)
    try:
        # 30秒タイムアウト
        result = await asyncio.wait_for(engine.predict(model_id, request.data), timeout=30.0)
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Prediction timed out")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 予期せぬエラーのハンドリング
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_id}/batch-predict", response_model=BatchPredictionResponse, summary="バッチ予測", description="複数データのバッチ予測を実行します（最大1000件）。")
async def batch_predict(model_id: int, request: BatchPredictionRequest, db: AsyncSession = Depends(get_db)):
    engine = InferenceEngine(db)
    try:
        results = await engine.batch_predict(model_id, request.data)
        return {"results": results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{model_id}/stats", response_model=StatsResponse, summary="推論統計", description="推論のレイテンシ統計などを取得します。")
async def get_stats(model_id: int, db: AsyncSession = Depends(get_db)):
    engine = InferenceEngine(db)
    stats = await engine.get_model_stats(model_id)
    return stats

@router.post("/route", response_model=RouteResponse, summary="ABテストルーティング", description="X-AB-Test-IDヘッダーに基づいてルーティングを行います。")
async def route_traffic(
    x_ab_test_id: int = Header(..., alias="X-AB-Test-ID", description="ABテストID"),
    db: AsyncSession = Depends(get_db)
):
    engine = InferenceEngine(db)
    try:
        model_id = await engine.route_ab_test(x_ab_test_id)
        return {"model_id": model_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
