from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

def utc_now():
    return datetime.now(timezone.utc)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class MLModel(Base):
    """
    MLモデル定義 (ML Model Definition)

    属性:
        id: モデルID
        name: モデル名
        version: バージョン
        framework: フレームワーク (PyTorch, TensorFlow, etc.)
        artifact_uri: アーティファクトのURI (S3パスなど)
        metrics: 評価指標 (JSON)
        status: ステータス (registered, deployed, archived)
        created_at: 作成日時
        updated_at: 更新日時
    """
    __tablename__ = "ml_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[str] = mapped_column(String)
    framework: Mapped[str] = mapped_column(String)
    artifact_uri: Mapped[str] = mapped_column(String)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String, default="registered")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    deployments: Mapped[List["DeployedModel"]] = relationship(back_populates="model")
    # ab_tests_a and ab_tests_b relationships could be added if needed, but omitted for brevity unless required.

class Experiment(Base):
    """
    実験 (Experiment)

    属性:
        id: 実験ID
        name: 実験名
        description: 説明
        tags: タグ (JSON)
        created_at: 作成日時
    """
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    runs: Mapped[List["Run"]] = relationship(back_populates="experiment")

class Run(Base):
    """
    実行 (Run)

    属性:
        id: 実行ID
        experiment_id: 実験ID
        status: ステータス (running, completed, failed)
        params: パラメータ (JSON)
        metrics: 指標 (JSON)
        start_time: 開始日時
        end_time: 終了日時
    """
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"))
    status: Mapped[str] = mapped_column(String)
    params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    experiment: Mapped["Experiment"] = relationship(back_populates="runs")

class DeployedModel(Base):
    """
    デプロイ済みモデル (Deployed Model)

    属性:
        id: デプロイID
        model_id: モデルID
        endpoint_url: エンドポイントURL
        traffic_split: トラフィック分割割合 (int)
        status: ステータス (active, inactive)
        created_at: 作成日時
    """
    __tablename__ = "deployed_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("ml_models.id"))
    endpoint_url: Mapped[str] = mapped_column(String)
    traffic_split: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    model: Mapped["MLModel"] = relationship(back_populates="deployments")

class ABTest(Base):
    """
    ABテスト (A/B Test)

    属性:
        id: テストID
        name: テスト名
        model_a_id: モデルA ID (コントロール)
        model_b_id: モデルB ID (チャレンジャー)
        traffic_ratio: トラフィック比率 (0.0 - 1.0)
        status: ステータス (scheduled, running, completed)
        start_time: 開始日時
        end_time: 終了日時
    """
    __tablename__ = "ab_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    model_a_id: Mapped[int] = mapped_column(ForeignKey("ml_models.id"))
    model_b_id: Mapped[int] = mapped_column(ForeignKey("ml_models.id"))
    traffic_ratio: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="scheduled")
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    model_a: Mapped["MLModel"] = relationship("MLModel", foreign_keys=[model_a_id])
    model_b: Mapped["MLModel"] = relationship("MLModel", foreign_keys=[model_b_id])
