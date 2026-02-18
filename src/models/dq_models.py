from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import String, Float, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base

class DQRule(Base):
    """
    データ品質ルール定義モデル

    Attributes:
        id (int): ルールID
        dataset_id (str): 対象データセットID
        rule_type (str): ルールの種類 (例: 'null_check', 'value_range')
        condition (dict): ルールの条件定義 (JSON)
        severity (str): 重大度 ('info', 'warning', 'critical')
    """
    __tablename__ = "dq_rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dataset_id: Mapped[str] = mapped_column(String, index=True)
    rule_type: Mapped[str] = mapped_column(String)
    condition: Mapped[Dict[str, Any]] = mapped_column(JSON)
    severity: Mapped[str] = mapped_column(String, default="warning")

class DQReport(Base):
    """
    データ品質レポートモデル

    Attributes:
        id (int): レポートID
        dataset_id (str): 対象データセットID
        overall_score (float): 総合品質スコア (0-100)
        issues (dict): 検出された問題点 (JSON)
        generated_at (datetime): 生成日時
    """
    __tablename__ = "dq_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dataset_id: Mapped[str] = mapped_column(String, index=True)
    overall_score: Mapped[float] = mapped_column(Float)
    issues: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
