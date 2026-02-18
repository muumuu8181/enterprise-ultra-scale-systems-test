# Step 6: 交通管理システム仕様 (STEP6_TRAFFIC.md)

## 1. 概要
都市全体の交通流を最適化し、渋滞の緩和、事故の早期発見、公共交通の円滑な運行を支援するシステム。

## 2. コンポーネント設計

### 2.1 信号制御最適化 (`src/services/traffic/signal_controller.py`)
- **クラス**: `TrafficSignalController`
- **機能**:
    - `optimize_cycle(intersection_id, current_flows) -> SignalPlan`: 交差点ごとの交通量（リアルタイム）に基づき、信号サイクル（青時間比率）を動的に最適化。
    - `coordinate_green_wave(road_id, speed) -> List[SignalPlan]`: 主要幹線道路において、車両が停止せずに通過できるよう連続した信号を同期させる（青波制御）。
    - `emergency_preemption(vehicle_id, route) -> None`: 救急車・消防車などの緊急車両が接近した際、優先的に青信号にする機能（現場急行支援）。

### 2.2 経路探索エンジン (`src/services/traffic/routing_engine.py`)
- **クラス**: `CityRoutingEngine`
- **機能**:
    - `find_route(origin, destination, mode, avoid_congestion) -> Route`: A*アルゴリズムをベースに、リアルタイムの渋滞情報や事故情報をコストとして考慮した最適経路探索。
    - `multimodal_route(origin, destination) -> MultimodalRoute`: バス、電車、徒歩、シェアサイクルなど複数の移動手段を組み合わせた経路案内。
    - `real_time_reroute(vehicle_id, current_route, incident_id) -> Route`: 走行中の車両に対し、突発的な事故や工事を回避するリルート提案。

### 2.3 スマートパーキング管理 (`src/services/traffic/parking_manager.py`)
- **クラス**: `SmartParkingManager`
- **機能**:
    - `find_available(location, radius_m, ev_required) -> List[ParkingLot]`: 現在地周辺の空き駐車場検索。EV充電器の有無など条件指定可。
    - `reserve(lot_id, user_id, duration_minutes) -> Reservation`: 駐車場の事前予約・決済。
    - `update_occupancy(lot_id, available_spaces) -> None`: センサーまたはカメラからの満空情報更新。

## 3. 主要アルゴリズム
- **適応的信号制御**: 強化学習またはルールベース制御による、交通量に応じたサイクル長の調整。
- **動的経路誘導**: 交通需要予測に基づき、特定の道路への集中を避けるよう車両を分散させる（システム最適）。
