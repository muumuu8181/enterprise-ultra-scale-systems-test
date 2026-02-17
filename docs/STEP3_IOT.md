### MQTTGateway クラス詳細仕様

**handle_message(topic: str, payload: bytes) -> None**
- topicパターン: `city/{zone_id}/device/{device_id}/{metric}`
- 処理フロー:
  1. topic解析 → device_id, metric_name 抽出
  2. デバイス認証チェック（Redisキャッシュ優先）
  3. payload デシリアライズ（MessagePack形式）
  4. 値の範囲チェック（デバイス種別ごとの正常値範囲）
  5. Kafka Producer で `sensor.raw` トピックに送信
  6. 異常値の場合は `sensor.anomaly` トピックにも送信
- スループット目標: 500K msg/sec / ノード
- 接続数: 最大10万デバイス / ノード

### SensorDataProcessor（Flink StreamTask）仕様
- 入力: Kafka `sensor.raw` トピック
- ウィンドウ: 10秒Tumbling Window
- 処理:
  1. device_id ごとにグループ化
  2. 10秒間の平均値・最大値・最小値・標準偏差を計算
  3. TimescaleDB に書き込み（COPY コマンド使用でバルク高速書き込み）
  4. Redisにリアルタイム値を更新（HSET device:{id}:latest）
  5. 閾値超過 → AlertService に送信
- 並列度: 32 (Kafka partition数に合わせる)
