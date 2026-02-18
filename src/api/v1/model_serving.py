from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from celery.result import AsyncResult

from src.core.database import get_db
from src.services.model_server import model_server, predict_async_task

router = APIRouter(prefix="/serving", tags=["Model Serving"])

# Schema definitions
class ModelLoadResponse(BaseModel):
    status: str
    message: str

class ModelHealthResponse(BaseModel):
    model_id: int
    status: str
    memory_usage: Optional[int] = None

class PredictRequest(BaseModel):
    model_id: int
    input_data: Any

class AsyncPredictResponse(BaseModel):
    job_id: str
    status: str

class PredictResultResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Any] = None

# Endpoints

@router.post("/models/{model_id}/load", response_model=ModelLoadResponse)
async def load_model(model_id: int, db: AsyncSession = Depends(get_db)):
    """
    モデルをロードし、ウォームアップを行います。
    """
    success = await model_server.load_model(model_id, db)
    if not success:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found or failed to load")
    return ModelLoadResponse(status="success", message=f"Model {model_id} loaded successfully")

@router.post("/models/{model_id}/unload", response_model=ModelLoadResponse)
async def unload_model(model_id: int):
    """
    モデルをアンロードします。
    """
    model_server.unload_model(model_id)
    return ModelLoadResponse(status="success", message=f"Model {model_id} unloaded")

@router.get("/models/{model_id}/health", response_model=ModelHealthResponse)
async def check_model_health(model_id: int):
    """
    モデルのヘルスチェックを行います。
    """
    is_loaded = model_server.health_check(model_id)
    if not is_loaded:
        raise HTTPException(status_code=404, detail="Model not loaded")

    return ModelHealthResponse(
        model_id=model_id,
        status="healthy",
        memory_usage=model_server.get_memory_usage()
    )

@router.post("/predict/async", response_model=AsyncPredictResponse)
async def predict_async(request: PredictRequest):
    """
    非同期推論リクエストを受け付けます (Celery)。
    """
    task = predict_async_task.delay(request.model_id, request.input_data)
    return AsyncPredictResponse(job_id=task.id, status="submitted")

@router.get("/predict/{job_id}/result", response_model=PredictResultResponse)
async def get_predict_result(job_id: str):
    """
    非同期推論の結果を取得します。
    """
    task_result = AsyncResult(job_id)

    response = PredictResultResponse(job_id=job_id, status=task_result.status)

    if task_result.ready():
        if task_result.successful():
            response.result = task_result.result
        else:
            response.status = "FAILED"
            response.result = {"error": str(task_result.result)}

    return response
