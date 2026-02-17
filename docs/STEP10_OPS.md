# Step 10: 運用・パフォーマンス仕様 (STEP10_OPS.md)

## 1. 概要
本システムの品質、安定性、およびスケーラビリティを保証するためのテスト戦略と運用管理の仕様。

## 2. テスト戦略

### 2.1 ユニットテスト (Unit Tests)
- **対象**: 各モジュールのアルゴリズム、ロジック。
- `tests/unit/test_signal_controller.py`: 信号最適化アルゴリズムが期待通りにサイクル長を計算するか検証。
- `tests/unit/test_routing_engine.py`: A*経路探索が最短経路を正しく導出するか、計算速度が要件を満たすか検証。
- `tests/unit/test_energy_optimizer.py`: 需要予測モデルの精度（RMSE < 5%）を検証。
- `tests/unit/test_flood_prediction.py`: 洪水リスクマップ生成のロジックが正しい入出力を行うか検証。

### 2.2 統合テスト (Integration Tests)
- **対象**: 複数コンポーネント間のデータ連携。
- `tests/integration/test_iot_pipeline.py`: デバイス(Mock) → MQTT → Kafka → Flink → DB までの一連のデータフローが正常に機能するか検証。
- `tests/integration/test_emergency_dispatch.py`: 緊急通報APIの呼び出しから、適切なユニットへの出動命令生成までの一連のワークフローを検証。

### 2.3 パフォーマンステスト (Performance Tests)
- **対象**: システム全体の負荷耐性と応答速度。
- `tests/performance/test_sensor_ingestion.py`: JMeterまたはLocustを使用し、1,000万 msg/sec の負荷をかけた際のシステム挙動（スループット、バックプレッシャー）を確認。

## 3. 性能基準 (SLA/SLO)

| 項目 | 目標値 | 備考 |
|------|--------|------|
| **IoTデータ取込み** | 10,000,000 msg/sec | Flink + Kafka の水平スケールにより達成。 |
| **交通信号最適化** | < 500ms | 全交差点の信号同期計算の完了時間。 |
| **デジタルツイン更新** | < 100ms | イベント発生からクライアント画面へのWebSocket配信完了まで。 |
| **緊急ディスパッチ** | < 10秒 | 通報受信から最適ユニットの選定および出動指令まで。 |
| **洪水予測** | < 30秒 | 気象データ更新からリスクマップ生成完了まで。 |
| **システム可用性** | 99.999% | 年間ダウンタイム約5分以内（Five Nines）。 |

## 4. 運用・監視 (Observability)
- **メトリクス**: Prometheus + Grafana によるリソース使用率、レイテンシ、エラー率の可視化。
- **ログ**: Fluentd + Elasticsearch (or Loki) によるログ集約と検索。
- **トレーシング**: Jaeger による分散トレーシングでボトルネック特定。
