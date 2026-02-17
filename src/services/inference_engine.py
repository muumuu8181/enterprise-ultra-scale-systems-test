import asyncio
import json
import random
import time
from typing import Any, Dict, List, Optional
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.ml_models import MLModel, DeployedModel, ABTest
from src.core.redis_client import redis_client

class InferenceEngine:
    """
    推論エンジン
    Inference Engine handling prediction, batch processing, and AB routing.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        # グローバルRedisクライアントを使用
        self.redis = redis_client
        # モックモデルキャッシュ (メモリ内)
        self.loaded_models = {}

    async def _load_model(self, model_id: int):
        """
        モデルロード (MLflow形式モック)
        Load model into memory (Mock).
        """
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]

        # モデル存在確認
        model = await self.db.get(MLModel, model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        # ロード処理のモック
        # 実際には mlflow.pyfunc.load_model(model.artifact_uri) など
        print(f"Loading model {model.name} from {model.artifact_uri}")

        # モック予測関数
        def mock_predict(data):
            # 処理時間のシミュレーション
            time.sleep(0.01)
            # 入力データ数分の予測値を返す
            return [random.random() for _ in range(len(data))]

        self.loaded_models[model_id] = mock_predict
        return mock_predict

    async def predict(self, model_id: int, input_data: List[Any]) -> Dict[str, Any]:
        """
        予測実行 (前処理、推論、後処理)
        Run prediction for a single request (can contain multiple data points).
        """
        start_time = time.time()

        predictor = await self._load_model(model_id)

        # 前処理 (モック: 何もしない)
        processed_data = input_data

        # 推論 (ブロッキング操作はスレッドプールで実行)
        loop = asyncio.get_event_loop()
        predictions = await loop.run_in_executor(None, predictor, processed_data)

        # 後処理
        results = {"predictions": predictions}

        # 統計記録 (非同期)
        latency = (time.time() - start_time) * 1000 # ms
        await self._update_stats(model_id, latency)

        return results

    async def batch_predict(self, model_id: int, batch_data: List[List[Any]]) -> List[Dict[str, Any]]:
        """
        バッチ予測 (並列処理)
        Batch prediction using asyncio.gather. Limit max concurrency if needed.
        """
        if len(batch_data) > 1000:
            raise ValueError("Batch size exceeds limit of 1000")

        # 各データポイントに対して予測タスクを作成
        tasks = [self.predict(model_id, item) for item in batch_data]
        results = await asyncio.gather(*tasks)
        return results

    async def _update_stats(self, model_id: int, latency_ms: float):
        """
        推論統計更新 (Redis)
        Update inference stats in Redis.
        """
        key_prefix = f"inference:stats:{model_id}"
        pipe = self.redis.pipeline()

        # カウントと合計レイテンシの更新
        await pipe.incr(f"{key_prefix}:count")
        await pipe.incrbyfloat(f"{key_prefix}:total_latency", latency_ms)

        # 直近のレイテンシをリストに保存 (パーセンタイル計算用、最大1000件保持)
        await pipe.lpush(f"{key_prefix}:latencies", latency_ms)
        await pipe.ltrim(f"{key_prefix}:latencies", 0, 999)
        await pipe.execute()

    async def get_model_stats(self, model_id: int) -> Dict[str, Any]:
        """
        推論統計取得 (Redis経由)
        Get inference stats (p50, p95, p99, throughput).
        """
        key_prefix = f"inference:stats:{model_id}"
        count = await self.redis.get(f"{key_prefix}:count")
        latencies = await self.redis.lrange(f"{key_prefix}:latencies", 0, -1)

        if not count or not latencies:
            return {"count": 0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "throughput": 0.0}

        latencies = sorted([float(x) for x in latencies])
        n = len(latencies)

        # シンプルなパーセンタイル計算
        def get_percentile(p):
            idx = int(n * p)
            return latencies[min(idx, n - 1)]

        return {
            "count": int(count),
            "p50": get_percentile(0.50),
            "p95": get_percentile(0.95),
            "p99": get_percentile(0.99),
            "throughput": float(count)  # 簡易実装: 総数のみ
        }

    async def route_ab_test(self, ab_test_id: int) -> int:
        """
        ABテストルーティング
        Route traffic based on AB test configuration.
        """
        stmt = select(ABTest).where(ABTest.id == ab_test_id, ABTest.status == "active")
        res = await self.db.execute(stmt)
        test = res.scalar_one_or_none()

        if not test:
            raise ValueError(f"Active AB Test {ab_test_id} not found")

        # トラフィック分割ロジック
        if random.random() < test.traffic_ratio:
            return test.model_b_id
        else:
            return test.model_a_id
