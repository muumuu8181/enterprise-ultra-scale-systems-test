import logging
import asyncio
import random
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis, from_url as redis_from_url

from src.models.ml_models import MLModel, ABTest

logger = logging.getLogger(__name__)

# Redis設定 (通常は設定ファイルから読み込む)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

_redis_client: Optional[Redis] = None

def get_redis_client() -> Redis:
    """Redisクライアントのシングルトンを取得"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis_from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    return _redis_client

class InferenceEngine:
    """
    推論エンジン
    予測実行、バッチ処理、ABテストのルーティングを担当します。
    """
    def __init__(self, db: AsyncSession, redis: Optional[Redis] = None):
        self.db = db
        self.redis = redis or get_redis_client()

    async def predict(
        self,
        model_id: int,
        input_data: Dict[str, Any],
        model: Optional[MLModel] = None
    ) -> Dict[str, Any]:
        """
        指定されたモデルで予測を実行します（非同期）。
        実際の推論処理はここではモック化されています。
        """
        if model is None:
            # モデル情報の取得 (キャッシュ推奨だがここではDBアクセス)
            stmt = select(MLModel).where(MLModel.id == model_id)
            result = await self.db.execute(stmt)
            model = result.scalars().first()

        if not model:
            raise ValueError(f"Model {model_id} not found")

        # 推論ロジックのシミュレーション (IO待ちなどを想定)
        await asyncio.sleep(0.01)

        # ダミーの予測結果
        prediction = {
            "model_id": model_id,
            "version": model.version,
            "prediction": random.random(), # 0.0-1.0のスコア
            "label": "positive" if random.random() > 0.5 else "negative"
        }

        logger.info(f"Prediction made by model {model_id}")
        return prediction

    async def batch_predict(self, model_id: int, input_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        複数の入力データに対して予測を実行します（asyncio.gather使用）。
        """
        # モデルを一度だけ取得して再利用 (DBセッションの並行利用を回避)
        stmt = select(MLModel).where(MLModel.id == model_id)
        result = await self.db.execute(stmt)
        model = result.scalars().first()

        if not model:
            raise ValueError(f"Model {model_id} not found")

        tasks = [self.predict(model_id, data, model=model) for data in input_data_list]
        results = await asyncio.gather(*tasks)
        return results

    async def route_ab_test(self, ab_test_id: int, user_id: str) -> int:
        """
        ユーザーをABテストの特定のモデルにルーティングします。
        Redisを使用してスティッキーセッション（同じユーザーは同じモデル）を実現します。

        戻り値:
            model_id (int): ルーティング先のモデルID
        """
        # Redisキャッシュキー
        cache_key = f"ab_test:{ab_test_id}:user:{user_id}"

        # 既存の割り当てを確認
        cached_model_id = await self.redis.get(cache_key)
        if cached_model_id:
            return int(cached_model_id)

        # ABテスト設定の取得
        stmt = select(ABTest).where(ABTest.id == ab_test_id)
        result = await self.db.execute(stmt)
        ab_test = result.scalars().first()

        if not ab_test:
            raise ValueError(f"AB Test {ab_test_id} not found")

        # トラフィック比率に基づいてルーティング
        # traffic_ratio は 0.0 - 1.0 (モデルAの割合) と仮定
        if random.random() < ab_test.traffic_ratio:
            selected_model_id = ab_test.model_a_id
        else:
            selected_model_id = ab_test.model_b_id

        # 結果をRedisにキャッシュ (有効期限: 24時間)
        await self.redis.set(cache_key, selected_model_id, ex=86400)

        logger.info(f"Routed user {user_id} to model {selected_model_id} for AB Test {ab_test_id}")
        return selected_model_id
