# Step 1: プロジェクト構造・用語集 (STEP1_OVERVIEW.md)

## 1. ディレクトリ構造
```
smart-city-os/
├── docs/                # 仕様書・ドキュメント
├── src/
│   ├── iot/
│   │   ├── gateway/         # IoTゲートウェイ (MQTT, LoRaWAN)
│   │   ├── device_mgmt/     # デバイス管理 (登録, OTA)
│   │   └── protocol/        # プロトコルアダプタ (MQTT/CoAP/LoRaWAN)
│   ├── pipeline/
│   │   ├── ingestion/       # データ取込み (Kafka Consumer)
│   │   ├── flink_jobs/      # Flinkストリーム処理ジョブ
│   │   └── batch/           # バッチ処理ジョブ
│   ├── digital_twin/        # デジタルツインエンジン
│   ├── services/
│   │   ├── traffic/         # 交通管理サービス
│   │   ├── energy/          # エネルギー管理サービス
│   │   ├── emergency/       # 緊急サービス
│   │   └── citizen/         # 市民ポータル
│   ├── analytics/           # データ分析・BI
│   └── api/                 # FastAPI エンドポイント (Gateway)
├── edge/                    # エッジノード設定
│   ├── k3s/                 # K3s マニフェスト
│   └── device_agents/       # エッジデバイスエージェント
└── tests/                   # テストコード
```

## 2. 用語集 (Glossary)

| 用語 | 英語 | 説明 |
|------|------|------|
| **IoT** | Internet of Things | モノのインターネット。センサーやデバイスがネットワークに接続されデータを送受信する仕組み。 |
| **MQTT** | Message Queuing Telemetry Transport | 軽量なパブリッシュ/サブスクライブ型のメッセージングプロトコル。IoTで広く使用される。 |
| **LoRaWAN** | Long Range Wide Area Network | 低消費電力で長距離通信を実現する無線通信規格（LPWAの一種）。 |
| **Digital Twin** | Digital Twin | 物理空間の情報をリアルタイムに収集し、デジタル空間上に再現した「双子」。シミュレーションに利用。 |
| **CEP** | Complex Event Processing | 複合イベント処理。複数のイベントストリームからパターンを検出し、リアルタイムに対応する技術。 |
| **GIS** | Geographic Information System | 地理情報システム。位置情報を持つデータを管理・加工・表示するシステム。 |
| **SCADA** | Supervisory Control and Data Acquisition | 監視制御システム。産業プロセスやインフラ設備の監視・制御を行う。 |
| **Edge Computing** | Edge Computing | データ発生源（デバイス）の近くでデータ処理を行う分散コンピューティングモデル。遅延低減や帯域節約に寄与。 |
| **Smart Grid** | Smart Grid | IT技術を活用して電力の需給を自動調整し、エネルギー効率を最適化する次世代送電網。 |
| **CIM** | City Information Modeling | 都市情報モデリング。BIM（Building Information Modeling）を都市レベルに拡張した概念。 |
| **Time Series** | Time Series | 時系列データ。時間の経過とともに観測されたデータの列（センサー計測値など）。 |
| **GDPR** | General Data Protection Regulation | EU一般データ保護規則。個人データの保護と取り扱いに関する厳格な規則。市民のプライバシー保護の基準とする。 |
