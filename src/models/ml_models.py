from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Text, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class Dataset(Base):
    """
    データセットモデル
    """
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    source_path: Mapped[str] = mapped_column(String, nullable=False)  # S3パスやローカルパス
    target_column: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    jobs: Mapped[list["TrainingJob"]] = relationship(back_populates="dataset")

class TrainingJob(Base):
    """
    AutoMLトレーニングジョブモデル
    """
    __tablename__ = "training_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    target_column: Mapped[str] = mapped_column(String, nullable=False)
    metric: Mapped[str] = mapped_column(String, default="accuracy")
    best_algorithm: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    best_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    artifact_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="jobs")
    model_versions: Mapped[list["ModelVersion"]] = relationship(back_populates="job")

class Model(Base):
    """
    モデルレジストリ - モデル定義
    """
    __tablename__ = "models"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    versions: Mapped[list["ModelVersion"]] = relationship(back_populates="model")

class ModelVersion(Base):
    """
    モデルレジストリ - モデルバージョン
    """
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id"), nullable=False)
    job_id: Mapped[Optional[str]] = mapped_column(ForeignKey("training_jobs.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, default="STAGING")  # STAGING, PRODUCTION, ARCHIVED
    artifact_path: Mapped[str] = mapped_column(String, nullable=False)
    metrics: Mapped[Optional[Dict[str, float]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    model: Mapped["Model"] = relationship(back_populates="versions")
    job: Mapped["TrainingJob"] = relationship(back_populates="model_versions")
