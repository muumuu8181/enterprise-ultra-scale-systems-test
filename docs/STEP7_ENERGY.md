# Step 7: エネルギー管理システム仕様 (STEP7_ENERGY.md)

## 1. 概要
都市全体の電力需給を最適化し、再生可能エネルギーの活用、ピークシフト、EV充電の効率化を実現するスマートグリッド管理システム。

## 2. コンポーネント設計

### 2.1 スマートグリッド最適化 (`src/services/energy/grid_optimizer.py`)
- **クラス**: `SmartGridOptimizer`
- **機能**:
    - `forecast_demand(zone_id, horizon_hours=24) -> DemandForecast`: 過去の消費パターン、気象予報、イベント情報などから、LSTMモデルを用いて未来（24時間先など）の電力需要を予測。
    - `balance_supply_demand(forecast, renewable_capacity) -> DispatchPlan`: 予測需要に対し、太陽光・風力などの再生可能エネルギー発電量を加味した最適な配電計画を策定。
    - `detect_fault(node_id, readings) -> FaultAlert`: 送電網上のセンサー値（電圧、周波数）から異常を検出し、停電や設備故障のアラートを発報。

### 2.2 EV充電管理 (`src/services/energy/ev_charging_manager.py`)
- **クラス**: `EVChargingManager`
- **機能**:
    - `find_charger(location, connector_type, radius_m) -> List[Charger]`: 利用可能な充電スポットの検索。
    - `smart_charge(charger_id, vehicle_id, grid_state) -> ChargingPlan`: 電力網の負荷状況に応じて充電速度を調整するスマートチャージ（ピークカット）。V2G (Vehicle-to-Grid) 対応も視野。
    - `balance_load(chargers: List) -> None`: 複数の充電器間で負荷を平準化し、局所的な過負荷を回避（ピークシフト）。

## 3. 主要アルゴリズム
- **需要予測**: 時系列解析（ARIMA, Prophet, LSTM）を用いた高精度な予測。
- **需給制御**: 数理最適化（線形計画法など）によるコスト最小化・再エネ最大化配分。
