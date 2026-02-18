from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict, Field

from src.models.ml_models import get_db, MLModel
from src.services.model_registry import ModelRegistryService

router = APIRouter(prefix="/models", tags=["models"])

# --- Request/Response Schemas ---

class ModelRegisterRequest(BaseModel):
    name: str = Field(..., description="モデル名")
    version: str = Field(..., description="バージョン")
    framework: str = Field(..., description="フレームワーク (e.g. pytorch, sklearn)")
    artifact_uri: str = Field(..., description="モデルアーティファクトのURI")
    metrics: Dict[str, Any] = Field(default={}, description="評価メトリクス")

class ModelResponse(BaseModel):
    id: int
    name: str
    version: str
    framework: str
    artifact_uri: str
    metrics: Dict[str, Any]
    status: str
    created_at: Any
    updated_at: Any

    model_config = ConfigDict(from_attributes=True)

class DeployRequest(BaseModel):
    endpoint_url: str = Field(..., description="デプロイ先エンドポイントURL")
    traffic_split: int = Field(100, description="トラフィック配分 (1-100)")

class DeployedModelResponse(BaseModel):
    id: int
    model_id: int
    endpoint_url: str
    status: str

    model_config = ConfigDict(from_attributes=True)

class ABTestCreateRequest(BaseModel):
    name: str
    model_a_id: int
    model_b_id: int
    traffic_ratio: float = Field(..., ge=0.0, le=1.0, description="モデルBへのトラフィック比率 (0.0-1.0)")

class ABTestResponse(BaseModel):
    id: int
    name: str
    model_a_id: int
    model_b_id: int
    traffic_ratio: float
    status: str

    model_config = ConfigDict(from_attributes=True)

# --- Endpoints ---

@router.post("/register", response_model=ModelResponse, summary="モデル登録", description="新しいMLモデルを登録します。")
async def register_model(request: ModelRegisterRequest, db: AsyncSession = Depends(get_db)):
    service = ModelRegistryService(db)
    try:
        model = await service.register_model(
            name=request.name,
            version=request.version,
            framework=request.framework,
            artifact_uri=request.artifact_uri,
            metrics=request.metrics
        )
        return model
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{model_id}", response_model=ModelResponse, summary="モデル詳細取得", description="指定されたIDのモデル詳細を取得します。")
async def get_model(model_id: int, db: AsyncSession = Depends(get_db)):
    service = ModelRegistryService(db)
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@router.get("", response_model=List[ModelResponse], summary="モデル一覧取得", description="フィルタ条件に基づいてモデル一覧を取得します。")
async def list_models(
    framework: Optional[str] = Query(None, description="フレームワークでフィルタ"),
    status: Optional[str] = Query(None, description="ステータスでフィルタ"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    service = ModelRegistryService(db)
    return await service.list_models(framework, status, skip, limit)

@router.post("/{model_id}/deploy", response_model=DeployedModelResponse, summary="モデルデプロイ", description="モデルを指定されたエンドポイントにデプロイします。")
async def deploy_model(model_id: int, request: DeployRequest, db: AsyncSession = Depends(get_db)):
    service = ModelRegistryService(db)
    try:
        deployment = await service.deploy_model(model_id, request.endpoint_url, request.traffic_split)
        return deployment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{model_id}", summary="モデルアーカイブ", description="モデルをアーカイブします（削除はしません）。")
async def archive_model(model_id: int, db: AsyncSession = Depends(get_db)):
    service = ModelRegistryService(db)
    try:
        success = await service.archive_model(model_id)
        if not success:
             raise HTTPException(status_code=404, detail="Model not found")
        return {"status": "archived"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ab-test", response_model=ABTestResponse, summary="ABテスト作成", description="新しいABテストを作成します。")
async def create_ab_test(request: ABTestCreateRequest, db: AsyncSession = Depends(get_db)):
    service = ModelRegistryService(db)
    try:
        test = await service.create_ab_test(request.name, request.model_a_id, request.model_b_id, request.traffic_ratio)
        return test
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/ab-test/{test_id}/results", summary="ABテスト結果", description="ABテストの結果（統計情報）を取得します。")
async def get_ab_test_results(test_id: int, db: AsyncSession = Depends(get_db)):
    service = ModelRegistryService(db)
    try:
        results = await service.get_ab_test_results(test_id)
        return results
    except ValueError as e:
         raise HTTPException(status_code=404, detail=str(e))
