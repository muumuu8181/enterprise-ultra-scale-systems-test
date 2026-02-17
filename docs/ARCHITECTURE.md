# アーキテクチャ設計書

## 1. 全体アーキテクチャ図 (High-Level)
本システムは、高いスケーラビリティと可用性を確保するため、マイクロサービスアーキテクチャを採用する。
メインロジックは Python (FastAPI) で実装し、極めて高いスループットが求められるランキング機能は Go言語で実装する。

### ダイアグラム概要
- **Client (Mobile App):** HTTP/2, WebSocket (for real-time events)
- **API Gateway (Istio/Nginx):** 認証、レート制限、負荷分散
- **Application Services:**
  - `Player Service`: ユーザー認証、基本情報管理 (Python)
  - `Gacha Service`: ガチャ抽選ロジック、確率計算 (Python)
  - `Inventory Service`: アイテム管理、倉庫機能 (Python)
  - `Billing Service`: 課金処理、レシート検証 (Python)
  - `Event Service`: イベント進行管理 (Python)
  - `Ranking Service`: ランキング集計・参照 (Go)
- **Data Stores:**
  - `PostgreSQL (Primary DB)`: プレイヤーデータ、ガチャ設定、課金履歴 (シャーディング検討)
  - `MongoDB`: ゲームプレイログ、監査証跡
  - `Redis`: セッション情報、ランキングデータ(Sorted Sets)、キャッシュ
- **Messaging:**
  - `Apache Kafka`: イベント駆動アーキテクチャの基盤 (ログ収集、非同期処理、分析パイプライン)

## 2. ディレクトリ構造と責任範囲
```
game-ops/
├── docs/               # 設計ドキュメント一式
├── src/
│   ├── core/           # ドメインロジック
│   │   ├── player/     # プレイヤー管理・認証
│   │   ├── gacha/      # ガチャエンジン (確率計算、天井)
│   │   ├── event/      # ライブイベント管理
│   │   ├── inventory/  # インベントリ・アイテム操作
│   │   ├── billing/    # 課金・決済フロー
│   │   ├── ranking/    # ランキングロジック (Go連携も考慮)
│   │   └── quest/      # クエスト進行管理
│   ├── infrastructure/ # インフラ層
│   │   ├── db/         # DB接続・ORM設定
│   │   ├── cache/      # Redisクライアント
│   │   ├── messaging/  # Kafkaプロデューサー/コンシューマー
│   │   └── security/   # 認証・暗号化ユーティリティ
│   └── api/            # FastAPI エンドポイント定義
├── db/
│   ├── schema/         # DDL SQLファイル
│   └── migrations/     # Alembicマイグレーションスクリプト
└── tests/
    ├── unit/           # 単体テスト
    ├── integration/    # 統合テスト
    └── performance/    # 負荷テスト (Locust)
```

## 3. 主要コンポーネント詳細

### 3.1 Backend (Python / FastAPI)
- **非同期処理:** `asyncio` を全面的に採用し、I/O待ちのオーバーヘッドを最小化。
- **ORM:** SQLAlchemy (Async) を使用。複雑なクエリとトランザクション管理を効率化。
- **Pydantic:** リクエスト/レスポンスのバリデーションとスキーマ定義。

### 3.2 Ranking Service (Go)
- **Redis Pipeline:** Redisへの書き込み・読み込みをバッチ化し、ネットワークRTTを削減。
- **Goroutines:** 高並列処理により、数万リクエスト/秒のスコア更新を処理。

### 3.3 Database (PostgreSQL)
- **Partitioning:** `gacha_histories` 等の巨大テーブルは、`player_id` ハッシュまたは時間範囲でパーティショニング。
- **Replication:** Read Replica を配置し、参照系クエリの負荷分散。

## 4. スケーラビリティ戦略
- **Stateless Application:** アプリケーションサーバーはステートレス設計とし、K8sのHPA (Horizontal Pod Autoscaler) で負荷に応じて自動スケール。
- **Database Sharding:** 将来的なデータ増大に備え、アプリケーションレベルでのシャーディングロジックを考慮 (Consistent Hashing)。
- **Caching Strategy:** 頻繁にアクセスされるマスタデータやプレイヤーの基本情報は Redis にキャッシュし、DB負荷を軽減。
