from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone

from src.services.model_registry import get_db
from src.services.drift_detector import DriftDetector
from src.models.monitoring_models import ModelAlert
from src.models.ml_models import MLModel

router = APIRouter()

# --- Pydantic Schemas ---

class AlertCreate(BaseModel):
    model_id: int
    metric: str
    threshold: float

class AlertResponse(BaseModel):
    id: int
    model_id: int
    metric: str
    threshold: float
    current_value: Optional[float]
    triggered_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DriftReportResponse(BaseModel):
    model_id: int
    drift_detected: bool
    psi_value: float
    threshold: float
    report_generated_at: str

class PerformanceResponse(BaseModel):
    model_id: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    evaluated_at: datetime

# --- Dependencies ---

def get_drift_detector(db: AsyncSession = Depends(get_db)):
    return DriftDetector(db)

# --- Endpoints ---

@router.get("/monitoring/{model_id}/drift", response_model=DriftReportResponse)
async def get_model_drift(
    model_id: int,
    detector: DriftDetector = Depends(get_drift_detector)
):
    """
    指定されたモデルのデータドリフト検知レポートを取得します。
    PSI > 0.2 の場合、自動再学習がトリガーされます。
    """
    try:
        report = await detector.generate_drift_report(model_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/monitoring/{model_id}/performance", response_model=PerformanceResponse)
async def get_model_performance(
    model_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    本番環境でのモデル精度モニタリング結果を取得します。
    """
    result = await db.execute(select(MLModel).where(MLModel.id == model_id))
    model = result.scalars().first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # メトリクスがあればそれを返す。なければデフォルト値。
    metrics = model.metrics or {}

    return {
        "model_id": model_id,
        "accuracy": metrics.get("accuracy", 0.0),
        "precision": metrics.get("precision", 0.0),
        "recall": metrics.get("recall", 0.0),
        "f1_score": metrics.get("f1_score", 0.0),
        "evaluated_at": datetime.now(timezone.utc)
    }

@router.post("/monitoring/alerts", response_model=AlertResponse)
async def create_alert(
    alert_in: AlertCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    新しい監視アラートを設定します。
    """
    # モデルの存在確認
    result = await db.execute(select(MLModel).where(MLModel.id == alert_in.model_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Model not found")

    alert = ModelAlert(
        model_id=alert_in.model_id,
        metric=alert_in.metric,
        threshold=alert_in.threshold
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert

@router.get("/monitoring/alerts/active", response_model=List[AlertResponse])
async def get_active_alerts(
    db: AsyncSession = Depends(get_db)
):
    """
    現在アクティブなアラート（トリガーされたもの）一覧を取得します。
    """
    stmt = select(ModelAlert).where(ModelAlert.triggered_at.is_not(None))
    result = await db.execute(stmt)
    return result.scalars().all()
