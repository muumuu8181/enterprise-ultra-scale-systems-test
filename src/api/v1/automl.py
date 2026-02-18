from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
import uuid
import os
import asyncio

from src.models.ml_models import TrainingJob, Dataset, Model, ModelVersion
from src.services.automl_service import AutoMLService
from src.database import get_db, AsyncSessionLocal

router = APIRouter(prefix="/automl", tags=["automl"])

# Pydantic Models
class AutoMLStartRequest(BaseModel):
    dataset_id: str
    target_column: str
    metric: str = "accuracy"
    task_type: str = "classification"

class AutoMLJobStatusResponse(BaseModel):
    id: str
    status: str
    error_message: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class AutoMLResultsResponse(BaseModel):
    id: str
    best_algorithm: Optional[str]
    best_params: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    model_config = ConfigDict(from_attributes=True)

class PromoteRequest(BaseModel):
    model_name: str
    description: Optional[str] = None

class PromoteResponse(BaseModel):
    model_version_id: str
    version: int
    status: str

async def run_automl_task(job_id: str, dataset_path: str, target_column: str, task_type: str):
    """
    バックグラウンドで実行されるAutoMLタスク
    """
    async with AsyncSessionLocal() as session:
        # Job取得
        result = await session.execute(select(TrainingJob).where(TrainingJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return # Should handle error

        job.status = "RUNNING"
        await session.commit()

        try:
            # サービス初期化と実行
            # dataset_pathが"mock"の場合はテスト用
            service = AutoMLService(dataset_path=dataset_path, target_column=target_column, task_type=task_type)

            # データロード
            await asyncio.to_thread(service.load_data)

            # 最適化
            best_algo, best_params, best_score = await asyncio.to_thread(service.select_best_algorithm)

            # レポート
            report = await asyncio.to_thread(service.generate_model_report)

            # ONNXエクスポート
            artifact_dir = f"artifacts/{job_id}"
            os.makedirs(artifact_dir, exist_ok=True)
            onnx_path = f"{artifact_dir}/model.onnx"
            await asyncio.to_thread(service.export_to_onnx, onnx_path)

            # 結果更新
            job.status = "COMPLETED"
            job.best_algorithm = best_algo
            job.best_params = best_params
            job.metrics = report
            job.artifact_path = onnx_path

        except Exception as e:
            job.status = "FAILED"
            job.error_message = str(e)
            print(f"AutoML Task Failed: {e}")
        finally:
            await session.commit()

@router.post("/start", response_model=AutoMLJobStatusResponse)
async def start_automl(request: AutoMLStartRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    AutoMLジョブを開始する
    """
    # Dataset確認
    result = await db.execute(select(Dataset).where(Dataset.id == request.dataset_id))
    dataset = result.scalar_one_or_none()

    # Datasetがない場合、テスト用にモックデータセットを作成するロジックを入れるか、エラーにするか。
    # ここではテスト容易性のため、dataset_id="mock"なら通す、あるいはDatasetテーブルになければ作る（簡易的）
    if not dataset:
        if request.dataset_id == "mock":
             dataset = Dataset(id="mock", name="Mock Dataset", source_path="mock", target_column=request.target_column)
             db.add(dataset)
             await db.flush()
        else:
             raise HTTPException(status_code=404, detail="Dataset not found")

    job_id = str(uuid.uuid4())
    job = TrainingJob(
        id=job_id,
        dataset_id=dataset.id,
        target_column=request.target_column,
        metric=request.metric,
        status="PENDING"
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # バックグラウンドタスク開始
    background_tasks.add_task(run_automl_task, job_id, dataset.source_path, request.target_column, request.task_type)

    return job

@router.get("/{job_id}/status", response_model=AutoMLJobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    ジョブのステータスを確認する
    """
    result = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/{job_id}/results", response_model=AutoMLResultsResponse)
async def get_job_results(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    ジョブの結果（メトリクスなど）を取得する
    """
    result = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Job not completed yet")

    return job

@router.post("/{job_id}/promote", response_model=PromoteResponse)
async def promote_model(job_id: str, request: PromoteRequest, db: AsyncSession = Depends(get_db)):
    """
    最良モデルをModel Registryに登録する
    """
    # ジョブ確認
    result = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Job not completed")

    # モデル確認または作成
    result = await db.execute(select(Model).where(Model.name == request.model_name))
    model = result.scalar_one_or_none()
    if not model:
        model = Model(id=str(uuid.uuid4()), name=request.model_name, description=request.description)
        db.add(model)
        await db.flush()

    # バージョン番号決定
    # 簡易的に現在バージョン数+1
    result = await db.execute(select(ModelVersion).where(ModelVersion.model_id == model.id))
    versions = result.scalars().all()
    next_version = len(versions) + 1

    model_version = ModelVersion(
        id=str(uuid.uuid4()),
        model_id=model.id,
        job_id=job.id,
        version=next_version,
        status="STAGING",
        artifact_path=job.artifact_path,
        metrics=job.metrics
    )
    db.add(model_version)
    await db.commit()

    return PromoteResponse(
        model_version_id=model_version.id,
        version=model_version.version,
        status=model_version.status
    )
