# Step 4: リアルタイムデータパイプライン仕様 (STEP4_PIPELINE.md)

## 1. 概要
Apache KafkaとApache Flinkを基盤とした、高スループット・低遅延なストリーム処理パイプラインの設計。

## 2. データフロー
`デバイス` → `MQTT/LoRaWAN Gateway` → `Kafka (Raw Topics)` → `Flink (Processing)` → `Kafka (Processed Topics)` → `TimescaleDB / Redis`

## 3. コンポーネント設計

### 3.1 データ取込み (`src/pipeline/ingestion/kafka_consumer.py`)
- **クラス**: `CityDataConsumer`
- **機能**:
    - `consume(topics, group_id) -> AsyncGenerator[Message]`: 指定トピックからのメッセージ非同期消費。
    - `route_to_handler(message) -> None`: メッセージタイプ（センサー、交通、アラート等）に応じたハンドラへのルーティング。

### 3.2 センサーデータ処理 (`src/pipeline/flink_jobs/sensor_processor.py`)
- **ジョブ**: `SensorDataProcessor` (Flink Job)
- **機能**:
    - `process_stream(source: KafkaSource) -> None`: ストリーム処理のメインループ。
    - `filter_outliers(reading: SensorReading) -> bool`: 統計的手法（Zスコア等）を用いた外れ値の除去。
    - `aggregate_5min(window: TimeWindow) -> AggregatedReading`: 5分間のタンブリングウィンドウ集計（平均、最大、最小）。
    - `detect_threshold_breach(reading, thresholds) -> Optional[Alert]`: 定義済み閾値を超えた場合のアラート生成。

### 3.3 交通流分析 (`src/pipeline/flink_jobs/traffic_processor.py`)
- **ジョブ**: `TrafficFlowAnalyzer` (Flink Job)
- **機能**:
    - `count_vehicles(camera_stream) -> VehicleCount`: 画像認識AIサービスと連携した車両カウント（またはエッジ側カウントの受信）。
    - `compute_congestion(flows: List[TrafficFlow]) -> CongestionMap`: 複数地点の流量からエリアの混雑度を算出。
    - `predict_congestion(historical, current) -> Prediction`: 直近データと過去パターンを用いた15分先の短期混雑予測。

## 4. パイプライン構成
- **Kafka Topics**:
    - `city-sensors-raw`: 生データ
    - `city-sensors-cleaned`: クレンジング済みデータ
    - `city-alerts`: アラートイベント
    - `city-traffic-flows`: 交通流データ
- **Flink State Backend**: RocksDB (大規模ステート管理用)
- **Checkpointing**: Exactly-once セマンティクス保証のため、定期的なチェックポイントを取得。
