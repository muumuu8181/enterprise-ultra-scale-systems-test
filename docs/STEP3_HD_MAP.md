# STEP 3: HDマップ管理・差分更新 (STEP3_HD_MAP.md)

## 1. 概要
本システムでは、自律走行に必要な高精度地図 (HD Map) として、Lanelet2フォーマットを採用する。また、相互運用性のためOpenDRIVE 1.8形式へのエクスポートもサポートする。地図データは静的な道路構造だけでなく、動的な規制情報や工事情報も管理し、差分更新 (Incremental Update) により1秒以内の配信を実現する。

## 2. 地図データ構造 (Lanelet2)

*   **Node**: 緯度・経度・標高を持つ点 (ID付き)。
*   **Way**: Nodeの順序付きリスト。白線や縁石を表す。
*   **Lanelet**: 左側・右側のBound (Way) によって定義される走行可能な車線。交通ルール (制限速度、通行方向) を属性として持つ。
*   **Regulatory Element**: 信号機、停止線、標識などの規制要素。Laneletに関連付けられる。
*   **Area**: 駐車場や広場などの面的な領域。

## 3. マップ管理クラス設計 (Python Implementation)

### 3.1 HDMapManager
地図のロード、経路探索用グラフの構築、クエリ処理を担当する。

```python
import lanelet2
from lanelet2.core import Lanelet, LaneletMap, Point3d, BoundingBox2d
from lanelet2.routing import RoutingGraph
from typing import List, Optional, Tuple

class HDMapManager:
    def __init__(self):
        self.map: Optional[LaneletMap] = None
        self.routing_graph: Optional[RoutingGraph] = None
        self.projector = lanelet2.projection.UtmProjector(lanelet2.io.Origin(35.6895, 139.6917))

    def load_lanelet2_map(self, osm_file: str) -> LaneletMap:
        """Lanelet2形式(.osm)の地図ファイルをロードする"""
        self.map = lanelet2.io.load(osm_file, self.projector)
        traffic_rules = lanelet2.traffic_rules.create(lanelet2.traffic_rules.Locations.Japan,
                                                      lanelet2.traffic_rules.Participants.Vehicle)
        self.routing_graph = lanelet2.routing.RoutingGraph(self.map, traffic_rules)
        return self.map

    def apply_map_patch(self, patch: 'MapDiffPatch') -> bool:
        """差分パッチを適用し、地図を部分的に更新する"""
        try:
            for elem in patch.added_elements:
                self.map.add(elem)
            for elem_id in patch.removed_element_ids:
                # 依存関係を考慮して削除
                self.remove_element_safe(elem_id)

            # ルーティンググラフの再構築（影響範囲のみが望ましい）
            self._rebuild_routing_graph()
            return True
        except Exception as e:
            print(f"Patch failed: {e}")
            return False

    def get_routing_graph(self) -> RoutingGraph:
        if not self.routing_graph:
            raise RuntimeError("Map not loaded")
        return self.routing_graph

    def find_shortest_path(self, start: Lanelet, end: Lanelet) -> Optional['LaneletPath']:
        """A*アルゴリズム等を用いて最短経路を探索"""
        route = self.routing_graph.getRoute(start, end)
        if route:
            return route.shortestPath()
        return None

    def get_regulatory_elements(self, area: BoundingBox2d) -> List['RegulatoryElement']:
        """指定エリア内の規制要素（信号、標識）を取得"""
        return self.map.regulatoryElementLayer.search(area)

    def validate_map_consistency(self) -> 'ValidationReport':
        """地図データの整合性チェック（孤立したLanelet、不整合な接続など）"""
        errors = []
        for lanelet in self.map.laneletLayer:
            if not lanelet.leftBound or not lanelet.rightBound:
                errors.append(f"Invalid bounds for lanelet {lanelet.id}")
        return ValidationReport(errors)

    def export_to_opendrive(self, output_path: str) -> None:
        """OpenDRIVE 1.8形式へ変換・出力"""
        # Lanelet2 to OpenDRIVE conversion logic
        pass

    def get_speed_limit(self, lanelet_id: int) -> float:
        """指定Laneletの制限速度を取得 (km/h -> m/s)"""
        ll = self.map.laneletLayer.get(lanelet_id)
        limit = ll.attributes.get("speed_limit", "50") # default 50km/h
        return float(limit) / 3.6

    def find_conflicting_lanelets(self, lanelet: Lanelet) -> List[Lanelet]:
        """交差またはマージする競合Laneletを取得"""
        return self.routing_graph.conflicting(lanelet)
```

### 3.2 MapUpdateService
クラウドからの差分更新を受け取るサービスクラス。

```python
class MapUpdateService:
    def __init__(self, region: str):
        self.current_version = "v1.0.0"
        self.region = region
        self.pending_patches = []

    def subscribe_to_updates(self, callback: callable):
        """MQTT/gRPCトピックを購読"""
        # topic: maps/updates/{region}
        pass

    def push_incremental_update(self, diff: 'MapDiff', affected_region: 'GeoRegion'):
        """クラウド側: 差分パッチの配信"""
        patch_data = self.serialize_diff(diff)
        # Verify signature
        if not self.validate_patch_integrity(patch_data):
            return

        # Publish to Edge/Vehicles
        self.mqtt_client.publish(f"maps/updates/{affected_region.id}", patch_data)

    def validate_patch_integrity(self, patch: 'MapDiffPatch') -> bool:
        """デジタル署名の検証とハッシュチェック"""
        return verify_signature(patch.signature, public_key) and check_hash(patch.data)

    def rollback_update(self, target_version: str) -> bool:
        """更新に問題があった場合のロールバック"""
        print(f"Rolling back to {target_version}")
        # Restore from snapshot
        return True

    def get_map_version(self) -> str:
        return self.current_version
```

## 4. 差分更新システム仕様

### 4.1 パッチフォーマット
Protocol Buffersを用いたバイナリ形式で配信する。

```protobuf
message MapPatch {
  string version_from = 1;
  string version_to = 2;
  int64 timestamp = 3;
  bytes signature = 4;

  repeated Lanelet added_lanelets = 5;
  repeated int64 removed_lanelet_ids = 6;
  repeated RegulatoryElement updated_regulations = 7;
}
```

### 4.2 更新フロー
1.  **Detection**: 路側機やプローブ車両が地図との不整合を検知。
2.  **Aggregation**: クラウドで不整合情報を集約・検証。
3.  **Generation**: 変更部分のみを抽出した`MapPatch`を生成。
4.  **Distribution**: 5G Broadcast (FeMBMS) または Geo-targeted MQTTで配信。
5.  **Application**: 車両側で受信し、メモリ上の地図グラフを動的に書き換え。この間、経路再計算が必要になる場合がある。
