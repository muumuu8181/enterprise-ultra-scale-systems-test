from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.ml_models import Base, utc_now

class ModelAlert(Base):
    """
    モデル監視アラート (Model Alert)

    属性:
        id: アラートID
        model_id: モデルID
        metric: メトリクス名 (e.g., "accuracy", "psi", "latency")
        threshold: 閾値
        current_value: 現在の値 (最後に確認した値)
        triggered_at: トリガー日時
        created_at: 作成日時
    """
    __tablename__ = "model_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("ml_models.id"), index=True)
    metric: Mapped[str] = mapped_column(String, index=True)
    threshold: Mapped[float] = mapped_column(Float)
    current_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationship to MLModel
    model: Mapped["MLModel"] = relationship("MLModel", foreign_keys=[model_id])
