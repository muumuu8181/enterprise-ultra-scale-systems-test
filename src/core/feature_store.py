import json
import asyncio
import hashlib
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os
from src.core.redis_client import redis_client

class FeatureStore:
    """
    特徴量ストア
    Feature Store managing feature registration, computation, and retrieval with Redis caching.
    """
    def __init__(self):
        # Use the global Redis client
        self.redis = redis_client
        self.ttl = 3600  # キャッシュ有効期限 (1時間)

    async def register_feature_set(self, name: str, schema: Dict[str, str], description: str) -> bool:
        """
        特徴量セットを登録する (スキーマバリデーション付き)
        Register a feature set with schema validation.
        """
        if not name:
            raise ValueError("Feature set name is required")
        if not isinstance(schema, dict) or not schema:
            raise ValueError("Invalid schema format")

        key = f"feature_store:schema:{name}"
        data = {
            "name": name,
            "schema": schema,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        await self.redis.set(key, json.dumps(data))
        return True

    async def get_features(self, feature_set_name: str, entity_ids: List[str]) -> Dict[str, Any]:
        """
        特徴量を取得する (Redisキャッシュ対応)
        Get features with Redis caching. If cache miss, compute features.
        """
        results = {}
        missing_ids = []

        # キャッシュから取得試行
        for entity_id in entity_ids:
            cache_key = f"feature_store:cache:{feature_set_name}:{entity_id}"
            cached_val = await self.redis.get(cache_key)
            if cached_val:
                results[entity_id] = json.loads(cached_val)
            else:
                missing_ids.append(entity_id)

        # キャッシュミスがあれば計算
        if missing_ids:
            computed_features = await self.compute_features(feature_set_name, missing_ids)
            for entity_id, features in computed_features.items():
                results[entity_id] = features
                # キャッシュに保存
                cache_key = f"feature_store:cache:{feature_set_name}:{entity_id}"
                await self.redis.set(cache_key, json.dumps(features), ex=self.ttl)

        return results

    async def compute_features(self, feature_set_name: str, entity_ids: List[str]) -> Dict[str, Any]:
        """
        特徴量計算パイプライン
        Compute features for the given entities. (Mock implementation)
        """
        # 特徴量セットの存在確認
        schema_key = f"feature_store:schema:{feature_set_name}"
        schema_json = await self.redis.get(schema_key)
        if not schema_json:
             # If not registered, we can't compute (or raise error)
             # For simplicity, we just log/raise
             raise ValueError(f"Feature set '{feature_set_name}' is not registered.")

        schema_data = json.loads(schema_json)
        schema = schema_data.get("schema", {})

        computed = {}
        for eid in entity_ids:
            # モック計算ロジック: エンティティIDに基づいて決定論的な値を生成
            # Mock computation logic: Generate deterministic values based on entity ID
            features = {}
            for field, type_hint in schema.items():
                seed = f"{eid}:{field}"
                val_hash = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
                if type_hint == "float":
                    features[field] = (val_hash % 1000) / 100.0
                elif type_hint == "int":
                    features[field] = val_hash % 100
                elif type_hint == "string":
                    features[field] = f"val_{val_hash % 100}"
                else:
                    features[field] = None

            features["_computed_at"] = datetime.now().isoformat()
            computed[eid] = features

        return computed

    async def get_training_data(self, feature_sets: List[str], entity_ids: List[str]) -> Dict[str, Any]:
        """
        学習用データの作成 (特徴量結合)
        Create training data by joining features from multiple sets (Point-in-time join simulation).
        """
        joined_data = {eid: {"entity_id": eid} for eid in entity_ids}

        for fs_name in feature_sets:
            features_map = await self.get_features(fs_name, entity_ids)
            for eid, features in features_map.items():
                # 特徴量セット名をプレフィックスとして結合
                for k, v in features.items():
                    if k != "_computed_at":
                        joined_data[eid][f"{fs_name}__{k}"] = v

        return joined_data
