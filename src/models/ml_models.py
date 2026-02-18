from typing import Optional, Any
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Float, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/ml_platform")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class MLModel(Base):
    """
    MLモデル定義
    Machine Learning Model Definition
    """
    __tablename__ = "ml_models"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[str] = mapped_column(String)
    framework: Mapped[str] = mapped_column(String)
    artifact_uri: Mapped[str] = mapped_column(String)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default={})
    status: Mapped[str] = mapped_column(String, default="registered")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Experiment(Base):
    """
    実験管理
    Experiment Management
    """
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tags: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Run(Base):
    """
    実験実行記録
    Experiment Run Record
    """
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True) # UUID
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"))
    status: Mapped[str] = mapped_column(String)
    params: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    metrics: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    artifacts: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class DeployedModel(Base):
    """
    デプロイ済みモデル
    Deployed Model Information
    """
    __tablename__ = "deployed_models"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("ml_models.id"))
    endpoint_url: Mapped[str] = mapped_column(String)
    traffic_split: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ABTest(Base):
    """
    ABテスト設定
    A/B Testing Configuration
    """
    __tablename__ = "ab_tests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    model_a_id: Mapped[int] = mapped_column(ForeignKey("ml_models.id"))
    model_b_id: Mapped[int] = mapped_column(ForeignKey("ml_models.id"))
    traffic_ratio: Mapped[float] = mapped_column(Float) # 0.0 to 1.0 (Traffic to Model B)
    status: Mapped[str] = mapped_column(String)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

# Dependency for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
