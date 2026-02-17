import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
from datetime import datetime

# センサーデータの簡易モデル
@dataclass
class SensorData:
    vehicle_id: str
    sensor_type: str
    detected_objects: List[Dict[str, Any]]
    timestamp: float

class CooperativePerception:
    """
    協調認識 (Cooperative Perception) クラス
    """
    def __init__(self, nats_client=None):
        self.nats_client = nats_client
        self.local_object_map: Dict[str, Any] = {}

    async def fuse_sensor_data(self, sensor_data_list: List[SensorData]) -> Dict[str, Any]:
        """
        複数車両センサーデータ融合を行う

        Args:
            sensor_data_list: 融合するセンサーデータのリスト

        Returns:
            融合後のオブジェクトマップ
        """
        fused_objects = {}

        for data in sensor_data_list:
            for obj in data.detected_objects:
                obj_id = obj.get("id")
                if not obj_id:
                    continue

                # 単純な上書き融合ロジック (本来はカルマンフィルタなどで位置推定精度を向上させる)
                # 信頼度(confidence)が高い方を採用するロジックの例
                existing = fused_objects.get(obj_id)
                if existing:
                    if obj.get("confidence", 0) > existing.get("confidence", 0):
                        fused_objects[obj_id] = obj
                else:
                    fused_objects[obj_id] = obj

        return fused_objects

    async def build_shared_object_map(self, fused_data: Dict[str, Any]) -> None:
        """
        共有オブジェクトマップ構築・更新

        Args:
            fused_data: 融合済みのセンサーデータ
        """
        # ローカルマップを更新
        self.local_object_map.update(fused_data)

        # 古いオブジェクトの削除処理などをここに追加可能
        # 例: 5秒以上更新がないオブジェクトを削除 (実装は省略)

    async def broadcast_perception_data(self, topic: str = "v2x.perception") -> None:
        """
        知覚データ配信 (NATS経由)

        Args:
            topic: 配信先のNATSトピック
        """
        if not self.nats_client:
            # クライアントが未接続の場合は何もしない
            return

        try:
            # マップデータをJSONに変換
            message = json.dumps(self.local_object_map)
            # NATSへPublish
            await self.nats_client.publish(topic, message.encode())
        except Exception as e:
            # エラーハンドリング
            print(f"Failed to broadcast perception data: {e}")
