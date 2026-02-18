from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.ml_models import Base, utc_now

class Pipeline(Base):
    """
    MLパイプライン定義 (ML Pipeline Definition)

    属性:
        id: パイプラインID
        name: パイプライン名
        steps: ステップ定義 (JSON)
        schedule_cron: 定期実行スケジュール (cron形式)
        status: ステータス (active, inactive, archived)
        last_run_at: 最終実行日時
        created_at: 作成日時
    """
    __tablename__ = "pipelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    steps: Mapped[dict] = mapped_column(JSON)
    schedule_cron: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    runs: Mapped[List["PipelineRun"]] = relationship(back_populates="pipeline", cascade="all, delete-orphan")


class PipelineRun(Base):
    """
    パイプライン実行履歴 (Pipeline Run History)

    属性:
        id: 実行ID
        pipeline_id: パイプラインID
        status: 実行ステータス (pending, running, completed, failed)
        started_at: 開始日時
        finished_at: 終了日時
        logs: 実行ログ (Text)
        artifacts: 生成アーティファクト (JSON)
    """
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pipeline_id: Mapped[int] = mapped_column(ForeignKey("pipelines.id"))
    status: Mapped[str] = mapped_column(String, default="pending")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    artifacts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    pipeline: Mapped["Pipeline"] = relationship(back_populates="runs")
