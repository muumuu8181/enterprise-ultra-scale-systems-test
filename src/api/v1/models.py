from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from src.services.model_registry import get_db, ModelRegistryService
from src.models.ml_models import MLModel, ABTest, DeployedModel

router = APIRouter()

# --- Pydantic Schemas ---

class ModelCreate(BaseModel):
    name: str = Field(..., description="モデル名")
    version: str = Field(..., description="バージョン")
    framework: str = Field(..., description="フレームワーク")
    artifact_uri: str = Field(..., description="アーティファクトURI")
    metrics: Optional[dict] = Field(None, description="メトリクス")

class ModelResponse(BaseModel):
    id: int
    name: str
    version: str
    framework: str
    artifact_uri: str
    metrics: Optional[dict]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DeploymentCreate(BaseModel):
    endpoint_url: str
    traffic_split: int = Field(100, ge=0, le=100)

class ABTestCreate(BaseModel):
    name: str
    model_a_id: int
    model_b_id: int
    traffic_ratio: float = Field(..., ge=0.0, le=1.0)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ABTestResponse(BaseModel):
    id: int
    name: str
    model_a_id: int
    model_b_id: int
    traffic_ratio: float
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# --- Dependencies ---

def get_registry_service(db: AsyncSession = Depends(get_db)):
    return ModelRegistryService(db)

# --- Endpoints ---

@router.post("/models/register", response_model=ModelResponse)
async def register_model(
    model_in: ModelCreate,
    service: ModelRegistryService = Depends(get_registry_service)
):
    """
    新しいMLモデルを登録します。
    """
    model = await service.register_model(
        name=model_in.name,
        version=model_in.version,
        framework=model_in.framework,
        artifact_uri=model_in.artifact_uri,
        metrics=model_in.metrics
    )
    return model

@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: int,
    service: ModelRegistryService = Depends(get_registry_service)
):
    """
    指定されたIDのモデル詳細を取得します。
    """
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@router.get("/models", response_model=List[ModelResponse])
async def list_models(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ModelRegistryService = Depends(get_registry_service)
):
    """
    登録済みモデルの一覧を取得します（ページネーション対応）。
    """
    return await service.list_models(skip=skip, limit=limit)

@router.post("/models/{model_id}/deploy")
async def deploy_model(
    model_id: int,
    deploy_in: DeploymentCreate,
    service: ModelRegistryService = Depends(get_registry_service)
):
    """
    モデルをデプロイします。
    """
    try:
        deployment = await service.deploy_model(
            model_id=model_id,
            endpoint_url=deploy_in.endpoint_url,
            traffic_split=deploy_in.traffic_split
        )
        return {"message": "Model deployed", "deployment_id": deployment.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/models/ab-test", response_model=ABTestResponse)
async def create_ab_test(
    ab_test_in: ABTestCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    新規ABテストを作成します。
    """
    # モデルの存在確認
    result_a = await db.execute(select(MLModel).where(MLModel.id == ab_test_in.model_a_id))
    model_a = result_a.scalars().first()
    result_b = await db.execute(select(MLModel).where(MLModel.id == ab_test_in.model_b_id))
    model_b = result_b.scalars().first()

    if not model_a or not model_b:
        raise HTTPException(status_code=404, detail="One or both models not found")

    ab_test = ABTest(
        name=ab_test_in.name,
        model_a_id=ab_test_in.model_a_id,
        model_b_id=ab_test_in.model_b_id,
        traffic_ratio=ab_test_in.traffic_ratio,
        start_time=ab_test_in.start_time,
        end_time=ab_test_in.end_time,
        status="scheduled"
    )
    db.add(ab_test)
    await db.commit()
    await db.refresh(ab_test)
    return ab_test
