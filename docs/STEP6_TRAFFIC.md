### TrafficSignalController クラス詳細仕様

**optimize_signal_timing(intersection_id, flows: TrafficFlowData) -> SignalPlan**
- アルゴリズム: Webster's optimal cycle length
  - C_opt = (1.5L + 5) / (1 - Y)  ← L=損失時間, Y=飽和交通量比の合計
- 入力: 各方向の現在の交通量・滞留長・歩行者数
- 出力: 各フェーズの青時間配分（最小5秒・最大90秒）
- 緊急車両優先: PREEMPT信号受信時は即座に緊急ルート方向を青に

### CityRoutingEngine クラス詳細仕様

**find_optimal_route(origin: Point, dest: Point, mode: str) -> Route**
- 道路グラフ: PostGIS + pgRouting (Dijkstra / A*)
- 考慮要素: 距離・速度制限・現在渋滞度・工事情報・時間帯制限
- mode: 'car' / 'emergency' / 'bicycle' / 'pedestrian'
- 緊急モード: 信号プリエンプション計画も同時生成
