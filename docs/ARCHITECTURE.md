# アーキテクチャ設計書 (ARCHITECTURE.md)

## 1. システム全体構成
本システムは、エッジ、クラウド、デジタルツインの3層構造で構成されるマイクロサービスアーキテクチャを採用する。

### 1.1 アーキテクチャ図 (概念)
```
[IoT Edge Nodes] --(MQTT/LoRaWAN)--> [Ingestion Gateway] --(Kafka)--> [Real-time Stream Processing (Flink)]
                                                                          |
                                                                          v
[Digital Twin Engine] <--(Updates)-- [Core Services] <--(Data)-- [Data Storage Layer]
       |                                   |                             |
       v                                   v                             v
[User Interfaces]                 [External Systems]             [Analytics / Batch Processing]
```

## 2. コンポーネント構成

### 2.1 エッジ層 (Edge Layer)
- **K3s Cluster**: エッジノード上でのコンテナオーケストレーション
- **Device Agents**: センサーデータ収集、初期フィルタリング、プロトコル変換
- **Gateway**: MQTT Broker, LoRaWAN Gateway

### 2.2 インジェスション・パイプライン層 (Ingestion & Pipeline Layer)
- **Message Broker**: Apache Kafka (高スループット、耐障害性)
- **Stream Processing**: Apache Flink (リアルタイム集計、異常検知、イベントトリガー)
- **Data Router**: メッセージの適切なトピックへのルーティング

### 2.3 データストレージ層 (Data Storage Layer)
- **TimescaleDB**: IoT時系列データの高速書き込み・クエリ
- **PostGIS**: 地理空間データの管理、空間検索
- **ClickHouse**: 大規模データの分析用カラムナストア
- **Redis**: リアルタイムキャッシュ、セッション管理

### 2.4 コアサービス層 (Core Services Layer)
各ドメインロジックを実装したマイクロサービス群。
- **Traffic Service**: 信号制御、経路探索、交通流分析
- **Energy Service**: スマートグリッド最適化、電力需要予測
- **Emergency Service**: 緊急車両ディスパッチ、防災アラート
- **Device Management**: デバイス登録、OTA、状態監視

### 2.5 デジタルツイン層 (Digital Twin Layer)
- **City Model Engine**: 都市の3Dモデルとリアルタイムデータを統合
- **Simulation Engine**: 交通流シミュレーション、災害シミュレーション
- **Visualization API**: フロントエンドへのデータ配信 (WebSocket)

## 3. データフロー
1. **データ発生**: センサーデバイスがデータを計測。
2. **エッジ処理**: K3s上のエッジノードでデータの前処理、圧縮。
3. **転送**: MQTT/LoRaWAN経由でクラウドゲートウェイへ送信。
4. **取り込み**: Kafkaトピックへメッセージをパブリッシュ。
5. **ストリーム処理**: FlinkジョブがKafkaからコンシュームし、リアルタイム集計、異常検知を実行。
6. **永続化**: 処理済みデータをTimescaleDB/PostGISへ保存。
7. **活用**:
    - デジタルツインへ状態更新をプッシュ。
    - 各サービスAPIがデータを参照し、制御指令を生成。
    - 分析バッチがClickHouseで長期トレンド分析。

## 4. 通信プロトコル
- **デバイス - エッジ**: Zigbee, BLE, Modbus
- **エッジ - クラウド**: MQTT (TLS), HTTP/2, CoAP
- **サービス間**: gRPC (内部通信), Kafka (非同期イベント)
- **クライアント - クラウド**: HTTPS (REST API), WebSocket (リアルタイム更新)

## 5. デプロイメント戦略
- **コンテナ基盤**: Kubernetesによるコンテナ管理
- **サービスメッシュ**: Istioによるトラフィック管理、mTLS、可観測性
- **スケーリング**: HPA (Horizontal Pod Autoscaler) による負荷に応じた自動スケール
