# Step 5: デジタルツイン仕様 (STEP5_DIGITAL_TWIN.md)

## 1. 概要
都市の物理空間をデジタル空間上に再現し、リアルタイムデータによる状態同期と、将来予測・シミュレーションを行う基盤。

## 2. コンポーネント設計

### 2.1 シティモデル管理 (`src/digital_twin/city_model.py`)
- **クラス**: `CityDigitalTwin`
- **機能**:
    - `update_entity(entity_type, entity_id, state) -> None`: センサーやサービスからのリアルタイムデータによるエンティティ状態更新。
    - `get_snapshot(entity_type, entity_id, timestamp) -> EntityState`: 指定時刻（現在または過去）のエンティティ状態取得。
    - `simulate_traffic_scenario(config: SimConfig) -> SimResult`: 交通流の変化（通行止め、新規ルート等）による影響シミュレーション。
    - `simulate_disaster(disaster_type, epicenter) -> ImpactAnalysis`: 災害発生時（地震、洪水等）の被害範囲および避難経路シミュレーション。

### 2.2 リアルタイム配信サーバー (`src/digital_twin/websocket_server.py`)
- **クラス**: `DigitalTwinWSServer` (FastAPI WebSocket)
- **機能**:
    - `broadcast_city_update(update: CityUpdate) -> None`: 全接続クライアントへの状態更新プッシュ配信（Pub/Sub）。
    - `subscribe_entity(client, entity_type, entity_id) -> None`: クライアントが関心を持つエンティティの購読管理。

## 3. データモデル
- **Entity**: 建物、道路、信号機、車両、人流などのオブジェクト。
- **State**: 位置、速度、状態（稼働中、故障中、混雑度）、環境値（気温、CO2）。
- **Snapshot**: 特定時刻における全EntityのStateの集合。JSONB形式でDBに保存。

## 4. フロントエンド・可視化
- **技術**: Unity Reflect (ハイエンド) / カスタムWebGL (ブラウザ向け: Three.js / deck.gl)
- **機能**:
    - 3Dマップ表示（地形、建物モデル）
    - リアルタイムデータオーバーレイ（ヒートマップ、アイコン移動）
    - インタラクティブ操作（クリックによる詳細表示、視点移動）
