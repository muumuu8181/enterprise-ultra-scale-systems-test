from typing import List, Optional, Dict, Any, Union
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_, and_
from sqlalchemy.exc import IntegrityError
import os

from src.models.ml_models import MLModel, DeployedModel, ABTest
from src.core.redis_client import redis_client

class ModelRegistryService:
    """
    モデルレジストリサービス
    Service for managing ML models, deployments, and lifecycle.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        # グローバルRedisクライアントを使用
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes

    async def register_model(self, name: str, version: str, framework: str, artifact_uri: str, metrics: Dict[str, Any]) -> MLModel:
        """
        モデルを登録する (バリデーション付き)
        Register a new model with version uniqueness check.
        """
        # バリデーション: 同名・同バージョンの確認
        stmt = select(MLModel).where(MLModel.name == name, MLModel.version == version)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError(f"Model '{name}' version '{version}' already exists.")

        new_model = MLModel(
            name=name,
            version=version,
            framework=framework,
            artifact_uri=artifact_uri,
            metrics=metrics,
            status="registered"
        )
        self.db.add(new_model)
        try:
            await self.db.commit()
            await self.db.refresh(new_model)
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Database integrity error during registration.")

        return new_model

    async def get_model(self, model_id: int) -> Optional[MLModel]:
        """
        モデル詳細を取得する (キャッシュ対応)
        Get model details with Redis caching.
        """
        cache_key = f"model_registry:model:{model_id}"

        # キャッシュ確認
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            try:
                data = json.loads(cached_data)
                # JSONからORMオブジェクトを再構築 (セッションには紐付かない - Detached)
                model = MLModel(**data)
                # datetime文字列をオブジェクトに変換
                if "created_at" in data and data["created_at"]:
                    model.created_at = datetime.fromisoformat(data["created_at"])
                if "updated_at" in data and data["updated_at"]:
                    model.updated_at = datetime.fromisoformat(data["updated_at"])
                return model
            except Exception:
                # キャッシュ破損時はDBへフォールバック
                pass

        # DB取得
        stmt = select(MLModel).where(MLModel.id == model_id)
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            # キャッシュ保存 (シリアライズ)
            model_dict = {
                "id": model.id,
                "name": model.name,
                "version": model.version,
                "framework": model.framework,
                "artifact_uri": model.artifact_uri,
                "metrics": model.metrics,
                "status": model.status,
                "created_at": model.created_at.isoformat() if model.created_at else None,
                "updated_at": model.updated_at.isoformat() if model.updated_at else None
            }
            await self.redis.set(cache_key, json.dumps(model_dict), ex=self.cache_ttl)

        return model

    async def list_models(self, framework: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 10) -> List[MLModel]:
        """
        モデル一覧を取得する (フィルター・ページネーション)
        List models with optional filters and pagination.
        """
        stmt = select(MLModel)
        if framework:
            stmt = stmt.where(MLModel.framework == framework)
        if status:
            stmt = stmt.where(MLModel.status == status)

        stmt = stmt.offset(skip).limit(limit).order_by(MLModel.id.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def deploy_model(self, model_id: int, endpoint_url: str, traffic_split: int = 100) -> DeployedModel:
        """
        モデルをデプロイする (Kubernetes Job作成のモック含む)
        Deploy a model to an endpoint.
        """
        # モデル存在確認 (DBから直接取得してセッションにアタッチ)
        model = await self.db.get(MLModel, model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found.")

        # Kubernetes Job作成のモック
        # Mock Kubernetes Job creation logic
        print(f"[Mock] Creating k8s deployment for model {model.name}:{model.version} at {endpoint_url}")

        # デプロイ記録作成
        deployment = DeployedModel(
            model_id=model_id,
            endpoint_url=endpoint_url,
            traffic_split=traffic_split,
            status="deployed"
        )
        self.db.add(deployment)

        # モデルステータス更新
        model.status = "deployed"
        self.db.add(model)

        await self.db.commit()
        await self.db.refresh(deployment)

        # キャッシュ無効化
        await self.redis.delete(f"model_registry:model:{model_id}")

        return deployment

    async def archive_model(self, model_id: int) -> bool:
        """
        モデルをアーカイブする (依存チェック付き)
        Archive a model. Check dependencies (deployments, AB tests) first.
        """
        # 依存チェック: アクティブなデプロイ
        stmt_deploy = select(DeployedModel).where(
            DeployedModel.model_id == model_id,
            DeployedModel.status == "deployed"
        )
        res_deploy = await self.db.execute(stmt_deploy)
        if res_deploy.scalars().first():
            raise ValueError("Cannot archive: Model is currently deployed.")

        # 依存チェック: アクティブなABテスト
        stmt_ab = select(ABTest).where(
            or_(ABTest.model_a_id == model_id, ABTest.model_b_id == model_id),
            ABTest.status == "active"
        )
        res_ab = await self.db.execute(stmt_ab)
        if res_ab.scalars().first():
            raise ValueError("Cannot archive: Model is used in an active AB test.")

        # アーカイブ処理
        model = await self.db.get(MLModel, model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found.")

        model.status = "archived"
        await self.db.commit()

        # キャッシュ無効化
        await self.redis.delete(f"model_registry:model:{model_id}")

        return True

    async def create_ab_test(self, name: str, model_a_id: int, model_b_id: int, traffic_ratio: float) -> ABTest:
        """
        ABテストを作成する
        Create a new AB Test.
        """
        # Validate models
        model_a = await self.db.get(MLModel, model_a_id)
        model_b = await self.db.get(MLModel, model_b_id)
        if not model_a or not model_b:
            raise ValueError("One or both models not found.")

        test = ABTest(
            name=name,
            model_a_id=model_a_id,
            model_b_id=model_b_id,
            traffic_ratio=traffic_ratio,
            status="active"
        )
        self.db.add(test)
        try:
            await self.db.commit()
            await self.db.refresh(test)
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("AB Test with this name already exists.")

        return test

    async def get_ab_test_results(self, test_id: int) -> Dict[str, Any]:
        """
        ABテスト結果を取得する (モック)
        Get AB Test results (Mock).
        """
        test = await self.db.get(ABTest, test_id)
        if not test:
            raise ValueError("AB Test not found.")

        # Mock results based on traffic ratio
        # In real system, query metrics/inference logs
        results = {
            "test_id": test.id,
            "model_a_id": test.model_a_id,
            "model_b_id": test.model_b_id,
            "traffic_ratio": test.traffic_ratio,
            "stats": {
                "model_a": {"requests": 1000, "conversions": 50},
                "model_b": {"requests": int(1000 * test.traffic_ratio), "conversions": int(50 * test.traffic_ratio * 1.1)},
            }
        }
        return results
