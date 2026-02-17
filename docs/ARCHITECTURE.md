# アーキテクチャ設計書 (ARCHITECTURE.md)

## 1. 全体アーキテクチャ

本システムは、高いスケーラビリティと保守性を確保するため、レイヤードアーキテクチャおよびドメイン駆動設計（DDD）の原則に基づいた構造を採用する。

### 1.1 アーキテクチャ図

```mermaid
graph TD
    Client[Client Apps (Web/Mobile)] --> LB[Load Balancer]
    LB --> API[API Gateway / FastAPI]

    subgraph "Core Domain Layer"
        Customer[Customer Service]
        Account[Account Service]
        Transaction[Transaction Service]
        Forex[Forex Service]
        Loan[Loan Service]
        Settlement[Settlement Service]
    end

    subgraph "Infrastructure Layer"
        DB_Adapter[DB Adapter (SQLAlchemy)]
        Msg_Adapter[Messaging Adapter (Kafka)]
        Cache_Adapter[Cache Adapter (Redis)]
        Sec_Adapter[Security Adapter]
    end

    API --> Customer
    API --> Account
    API --> Transaction
    API --> Forex
    API --> Loan
    API --> Settlement

    Customer --> DB_Adapter
    Account --> DB_Adapter
    Transaction --> DB_Adapter

    Transaction --> Msg_Adapter
    Transaction --> Cache_Adapter
```

## 2. ディレクトリ構造

`banking-core/` プロジェクトの標準的なディレクトリ構成は以下の通りである。

```
banking-core/
├── docs/                  # 仕様書・設計書 (本ドキュメント群)
├── src/
│   ├── core/              # ドメインロジック・ビジネスルール
│   │   ├── customer/      # 顧客管理 (CIF, KYC, Risk)
│   │   ├── account/       # 口座管理 (Ledger, Balance)
│   │   ├── transaction/   # 取引処理 (Deposit, Withdrawal, Transfer)
│   │   ├── forex/         # 為替 (Exchange Rates, SWIFT)
│   │   ├── loan/          # 融資 (Lending, Repayment)
│   │   └── settlement/    # 決済 (RTGS, Net Settlement)
│   ├── infrastructure/    # 技術的関心事の実装
│   │   ├── db/            # DB接続・リポジトリ基底クラス
│   │   ├── transaction/   # ACID制御・分散トランザクション (Saga/2PC)
│   │   ├── security/      # 認証・暗号化 (HSM/OAuth)
│   │   ├── audit/         # 監査ログ
│   │   ├── cache/         # Redis キャッシュ制御
│   │   └── messaging/     # Kafka イベントパブリッシャー
│   └── api/               # FastAPI エンドポイント・ルーティング
├── db/
│   ├── schema/            # DDL SQL ファイル（50ファイル以上）
│   ├── migrations/        # Alembic マイグレーションスクリプト
│   └── seeds/             # テストデータ・初期マスタ
└── tests/
    ├── unit/              # 単体テスト (Pytest)
    ├── integration/       # 結合テスト
    └── performance/       # 負荷テスト (Locust)
```

## 3. レイヤーの責務

### 3.1 API Layer (`src/api`)
- 外部からのHTTPリクエストを受け付け、入力検証（Pydantic）を行う。
- 適切なCoreサービスのメソッドを呼び出し、結果をレスポンスとして返す。
- 認証ミドルウェアによるアクセストークン検証を行う。

### 3.2 Core Layer (`src/core`)
- ビジネスロジックの中核。
- ドメインモデル、ドメインサービス、ビジネスルールを含む。
- インフラストラクチャ層の具体的な実装には依存せず、抽象インターフェース（Repository Interface等）のみに依存する（依存性逆転の原則）。

### 3.3 Infrastructure Layer (`src/infrastructure`)
- データベース、メッセージキュー、外部API、セキュリティ機能などの技術的詳細を実装する。
- Core層で定義されたリポジトリインターフェースの実装を提供する。
- 分散トランザクション制御や監査ログの永続化を担当する。

## 4. データフローとトランザクション

### 4.1 同期処理（勘定系トランザクション）
1. APIがリクエストを受信。
2. Transaction Serviceがビジネスロジックを実行。
3. Unit of Work パターンを用いて、DBへの変更をアトミックにコミット。
4. 処理結果をクライアントに返却。

### 4.2 非同期処理（情報系・外部連携）
1. 勘定系トランザクション完了後、OutboxパターンによりイベントをDBに保存。
2. バックグラウンドプロセスがイベントをKafkaにパブリッシュ。
3. コンシューマー（通知サービス、分析基盤等）がイベントを処理。

## 5. セキュリティ設計

- **認証・認可**: RBAC (Role-Based Access Control) を実装。
- **データ保護**: 個人情報（PII）はカラムレベルで暗号化して保存。
- **監査**: 誰がいつ何をしたかを `audit_logs` テーブルに改ざん検知可能な形式で記録。
