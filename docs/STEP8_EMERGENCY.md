# Step 8: 緊急サービス・防災仕様 (STEP8_EMERGENCY.md)

## 1. 概要
災害発生時の迅速な情報収集、避難誘導、および救急・消防活動の効率化を支援する緊急時対応システム。

## 2. コンポーネント設計

### 2.1 緊急通報・ディスパッチセンター (`src/services/emergency/dispatch_center.py`)
- **クラス**: `EmergencyDispatchSystem`
- **機能**:
    - `receive_call(caller_location, incident_type) -> Incident`: 119番通報やIoTセンサーからの異常検知をインシデントとして登録。
    - `dispatch_unit(incident_id, unit_type) -> DispatchOrder`: 現場に最も近い救急車・消防車を検索し、出動命令を自動生成（最近傍探索）。
    - `coordinate_response(incident_id) -> IncidentPlan`: 警察、消防、病院など複数機関への情報共有と連携指示。
    - `send_alert(zone_id, alert_type, message) -> None`: 該当地域の市民に対し、スマートフォンやサイネージを通じて緊急速報（J-ALERT連携）を配信。

### 2.2 洪水・災害リスク予測 (`src/services/emergency/flood_prediction.py`)
- **クラス**: `FloodRiskAnalyzer`
- **機能**:
    - `predict_flood(rainfall_forecast, river_levels) -> FloodRiskMap`: 気象予報（降水量）と河川水位データから、浸水リスクエリアをシミュレーション予測。
    - `evacuation_routing(affected_zones, shelters) -> List[EvacuationRoute]`: 浸水エリアを回避し、安全な避難所へ誘導する避難経路を算出・提示。

## 3. 主要アルゴリズム
- **ユニット配置最適化**: 現在地、交通状況、出動可能性を考慮したリソース割り当て（配送計画問題の応用）。
- **浸水シミュレーション**: 地形データ（DEM）と水理モデルを用いた氾濫解析。
