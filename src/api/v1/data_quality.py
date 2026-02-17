from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

from src.models.dq_models import DQRule, DQReport
from src.services.data_validator import DataValidator

# データベース設定
# 本番環境では環境変数やconfigファイルから読み込むべきだが、
# ここでは簡易実装としてSQLiteを使用する。
# テスト実行時などに競合しないよう、インメモリまたはファイルベースDBを選択可能にする。
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dq_database.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# アプリケーション起動時にテーブルを作成するためのヘルパー
# alembicを使用するのが正道だが、簡易実行のためにここに配置
async def init_dq_db():
    from src.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

router = APIRouter()
validator = DataValidator()

# --- Pydantic Schemas ---

class RuleCreate(BaseModel):
    dataset_id: str
    rule_type: str
    condition: Dict[str, Any]
    severity: str = "warning"

class RuleResponse(RuleCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ReportResponse(BaseModel):
    id: int
    dataset_id: str
    overall_score: float
    issues: Optional[Dict[str, Any]]
    generated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Endpoints ---

@router.on_event("startup")
async def startup_event():
    """
    アプリケーション起動時にデータベースを初期化します。
    """
    if not os.getenv("TESTING"):
        await init_dq_db()

@router.post("/rules", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(rule: RuleCreate, db: AsyncSession = Depends(get_db)):
    """
    データ品質ルールを設定します。
    """
    new_rule = DQRule(
        dataset_id=rule.dataset_id,
        rule_type=rule.rule_type,
        condition=rule.condition,
        severity=rule.severity
    )
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    return new_rule

@router.post("/validate/{dataset_id}", response_model=ReportResponse)
async def validate_dataset(dataset_id: str, db: AsyncSession = Depends(get_db)):
    """
    指定されたデータセットのバリデーションを実行し、レポートを生成します。
    """
    # 1. ルール取得 (今回は使用していないが、将来的にルールに基づいたチェックを行う拡張ポイント)
    # result = await db.execute(select(DQRule).where(DQRule.dataset_id == dataset_id))
    # rules = result.scalars().all()

    # 2. データ取得
    df = validator.get_dataset_data(dataset_id)
    if df.empty:
        raise HTTPException(status_code=404, detail="Dataset not found or empty")

    # 3. チェック実行
    null_report = validator.check_nulls(df)
    dup_rate = validator.check_duplicates(df)
    dist_report = validator.check_distribution(df)

    # スコア計算
    score = validator.generate_quality_score(null_report, dup_rate, dist_report)

    issues = {
        "null_check": null_report,
        "duplicate_rate": dup_rate,
        "distribution_stats": dist_report
    }

    # 4. レポート保存
    report = DQReport(
        dataset_id=dataset_id,
        overall_score=score,
        issues=issues
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return report

@router.get("/reports/{dataset_id}", response_model=List[ReportResponse])
async def get_reports(dataset_id: str, db: AsyncSession = Depends(get_db)):
    """
    指定されたデータセットの品質レポート履歴を取得します。
    """
    result = await db.execute(
        select(DQReport)
        .where(DQReport.dataset_id == dataset_id)
        .order_by(DQReport.generated_at.desc())
    )
    reports = result.scalars().all()
    return reports
