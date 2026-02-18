import logging
import os
from typing import List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update
from src.models.ml_models import Base, MLModel, DeployedModel, Experiment, Run

# ロガー設定
logger = logging.getLogger(__name__)

# データベース設定 (通常は設定ファイルから読み込む)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ml_platform.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def init_models():
    """テーブルを作成するユーティリティ"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """FastAPI用のDBセッション依存関係"""
    async with AsyncSessionLocal() as session:
        yield session

class ModelRegistryService:
    """
    モデル管理サービス
    モデルの登録、取得、一覧、デプロイ、アーカイブを担当します。
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_model(
        self,
        name: str,
        version: str,
        framework: str,
        artifact_uri: str,
        metrics: Optional[dict] = None
    ) -> MLModel:
        """
        新しいMLモデルを登録します。
        """
        model = MLModel(
            name=name,
            version=version,
            framework=framework,
            artifact_uri=artifact_uri,
            metrics=metrics,
            status="registered"
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        logger.info(f"Model registered: {model.id} ({model.name} v{model.version})")
        return model

    async def get_model(self, model_id: int) -> Optional[MLModel]:
        """
        モデルIDによるモデルの取得
        """
        result = await self.db.execute(select(MLModel).where(MLModel.id == model_id))
        return result.scalars().first()

    async def list_models(self, skip: int = 0, limit: int = 100) -> List[MLModel]:
        """
        モデル一覧の取得（ページネーション対応）
        """
        result = await self.db.execute(select(MLModel).offset(skip).limit(limit))
        return result.scalars().all()

    async def deploy_model(self, model_id: int, endpoint_url: str, traffic_split: int = 100) -> DeployedModel:
        """
        モデルをデプロイ状態として記録します。
        """
        # モデルの存在確認
        model = await self.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        # デプロイ情報の作成
        deployment = DeployedModel(
            model_id=model_id,
            endpoint_url=endpoint_url,
            traffic_split=traffic_split,
            status="active"
        )
        self.db.add(deployment)

        # モデルステータスの更新
        model.status = "deployed"
        self.db.add(model)

        await self.db.commit()
        await self.db.refresh(deployment)
        logger.info(f"Model deployed: {model_id} to {endpoint_url}")
        return deployment

    async def archive_model(self, model_id: int) -> Optional[MLModel]:
        """
        モデルをアーカイブします（論理削除やステータス変更）。
        """
        model = await self.get_model(model_id)
        if not model:
            return None

        model.status = "archived"
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        logger.info(f"Model archived: {model_id}")
        return model
