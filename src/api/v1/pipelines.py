from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from src.services.model_registry import get_db
from src.models.pipeline_models import Pipeline, PipelineRun
from src.services.pipeline_executor import PipelineExecutor

router = APIRouter()

# --- Pydantic Schemas ---

class PipelineCreate(BaseModel):
    name: str = Field(..., description="パイプライン名")
    steps: dict = Field(..., description="ステップ定義 (JSON)")
    schedule_cron: Optional[str] = Field(None, description="cron形式のスケジュール")

class PipelineResponse(BaseModel):
    id: int
    name: str
    steps: dict
    schedule_cron: Optional[str]
    status: str
    last_run_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PipelineRunResponse(BaseModel):
    id: int
    pipeline_id: int
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    logs: Optional[str]
    artifacts: Optional[dict]

    model_config = ConfigDict(from_attributes=True)

# --- Endpoints ---

@router.post("/pipelines", response_model=PipelineResponse)
async def create_pipeline(
    pipeline_in: PipelineCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    新しいパイプラインを作成します。
    """
    pipeline = Pipeline(
        name=pipeline_in.name,
        steps=pipeline_in.steps,
        schedule_cron=pipeline_in.schedule_cron
    )
    db.add(pipeline)
    await db.commit()
    await db.refresh(pipeline)
    return pipeline

@router.get("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    指定されたIDのパイプライン詳細を取得します。
    """
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalars().first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline

@router.post("/pipelines/{pipeline_id}/trigger", response_model=dict)
async def trigger_pipeline(
    pipeline_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    パイプラインの手動実行をトリガーします。
    """
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalars().first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    executor = PipelineExecutor(db)
    # 簡易実装: リクエスト内で実行を待機して返す
    run = await executor.execute_pipeline(pipeline_id)

    if not run:
         raise HTTPException(status_code=500, detail="Failed to start execution")

    return {"message": "Execution started", "run_id": run.id}

@router.get("/pipelines/{pipeline_id}/runs", response_model=List[PipelineRunResponse])
async def list_pipeline_runs(
    pipeline_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    パイプラインの実行履歴を取得します。
    """
    result = await db.execute(select(PipelineRun).where(PipelineRun.pipeline_id == pipeline_id))
    runs = result.scalars().all()
    return runs

@router.delete("/pipelines/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    パイプラインを削除します。
    """
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalars().first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    await db.delete(pipeline)
    await db.commit()
    return {"message": "Pipeline deleted"}
