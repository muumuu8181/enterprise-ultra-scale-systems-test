from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict, Field

from src.models.ml_models import get_db, Experiment, Run
from src.services.experiment_tracker import ExperimentTracker

router = APIRouter(prefix="/experiments", tags=["experiments"])

# --- Schemas ---

class ExperimentCreateRequest(BaseModel):
    name: str = Field(..., description="実験名")
    description: Optional[str] = Field(None, description="実験の説明")
    tags: Optional[Dict[str, Any]] = Field(None, description="タグ")

class ExperimentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    tags: Optional[Dict[str, Any]]
    created_at: Any

    model_config = ConfigDict(from_attributes=True)

class RunResponse(BaseModel):
    id: str
    experiment_id: int
    status: str
    params: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    start_time: Any
    end_time: Any

    model_config = ConfigDict(from_attributes=True)

class MetricsLogRequest(BaseModel):
    metrics: Dict[str, float] = Field(..., description="記録するメトリクス (key: value)")

class ParamsLogRequest(BaseModel):
    params: Dict[str, Any] = Field(..., description="記録するパラメータ (key: value)")

class RunFinishRequest(BaseModel):
    status: str = Field("completed", description="完了ステータス")

# --- Endpoints ---

@router.post("", response_model=ExperimentResponse, summary="実験作成", description="新しい実験を作成します。")
async def create_experiment(request: ExperimentCreateRequest, db: AsyncSession = Depends(get_db)):
    tracker = ExperimentTracker(db)
    try:
        exp = await tracker.create_experiment(request.name, request.description, request.tags)
        return exp
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{exp_id}/runs", response_model=RunResponse, summary="Run開始", description="実験の新しいRunを開始します。")
async def start_run(exp_id: int, db: AsyncSession = Depends(get_db)):
    tracker = ExperimentTracker(db)
    try:
        run = await tracker.start_run(exp_id)
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{exp_id}/runs/{run_id}/metrics", response_model=RunResponse, summary="メトリクス記録", description="Runのメトリクスを記録します。")
async def log_metrics(exp_id: int, run_id: str, request: MetricsLogRequest, db: AsyncSession = Depends(get_db)):
    tracker = ExperimentTracker(db)
    try:
        # Note: exp_id check could be added here
        run = await tracker.log_metrics(run_id, request.metrics)
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{exp_id}/runs/{run_id}/params", response_model=RunResponse, summary="パラメータ記録", description="Runのパラメータを記録します。")
async def log_params(exp_id: int, run_id: str, request: ParamsLogRequest, db: AsyncSession = Depends(get_db)):
    tracker = ExperimentTracker(db)
    try:
        run = await tracker.log_params(run_id, request.params)
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{exp_id}/runs/{run_id}/finish", response_model=RunResponse, summary="Run完了", description="Runを完了状態にします。")
async def finish_run(exp_id: int, run_id: str, request: RunFinishRequest, db: AsyncSession = Depends(get_db)):
    tracker = ExperimentTracker(db)
    try:
        run = await tracker.finish_run(run_id, request.status)
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{exp_id}/runs", response_model=List[RunResponse], summary="Run一覧", description="実験のRun一覧を取得します。")
async def get_runs(
    exp_id: int,
    sort_by: str = Query("start_time", description="ソートキー"),
    order: str = Query("desc", description="順序 (asc/desc)"),
    db: AsyncSession = Depends(get_db)
):
    tracker = ExperimentTracker(db)
    return await tracker.get_runs(exp_id, sort_by, order)

@router.get("/compare", response_model=List[RunResponse], summary="複数Run比較", description="複数のRunIDを指定して比較します。")
async def compare_runs(run_ids: List[str] = Query(..., description="比較するRun IDのリスト"), db: AsyncSession = Depends(get_db)):
    stmt = select(Run).where(Run.id.in_(run_ids))
    result = await db.execute(stmt)
    runs = result.scalars().all()
    return list(runs)
