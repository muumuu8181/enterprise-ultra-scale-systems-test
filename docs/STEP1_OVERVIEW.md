# Step 1: プロジェクト構造・要件定義 (STEP1_OVERVIEW.md)

## 1. プロジェクトの目的
本ドキュメントは、「銀行コアバンキングシステム（勘定系・情報系統合）」開発プロジェクトの初期フェーズ（Step 1）におけるプロジェクト構造と基本要件を定義するものである。

## 2. 目標と制約
- **目標コード量**: 250,000行以上（最終）
- **性能目標**: 10,000 TPS, レスポンス1秒以内
- **可用性目標**: 99.999%
- **開発言語**: Python (FastAPI)
- **データベース**: PostgreSQL 15

## 3. ディレクトリ構造の詳細

プロジェクトルート `banking-core/` 配下の構造は以下の通り定義する。

### 3.1 ドキュメント (`docs/`)
仕様書、設計書を格納する。

### 3.2 ソースコード (`src/`)
- **core/**: ビジネスロジック（ドメイン層）
    - `customer/`: 顧客管理（CIF）
    - `account/`: 口座管理（Ledger）
    - `transaction/`: 取引処理（Core Banking）
    - `forex/`: 外国為替
    - `loan/`: 融資・ローン
    - `settlement/`: 決済・清算
- **infrastructure/**: 技術基盤（インフラ層）
    - `db/`: データベース接続
    - `transaction/`: ACID・分散トランザクション制御
    - `security/`: セキュリティ基盤
    - `audit/`: 監査ログ
    - `cache/`: キャッシュ制御
    - `messaging/`: 非同期メッセージング
- **api/**: Web API（インターフェース層）
    - FastAPI ルーター定義

### 3.3 データベース (`db/`)
- `schema/`: DDL (SQLファイル)
- `migrations/`: DBマイグレーションスクリプト (Alembic)
- `seeds/`: 初期データ・テストデータ

### 3.4 テスト (`tests/`)
- `unit/`: 単体テスト
- `integration/`: 結合テスト
- `performance/`: 性能テスト (Locust)

## 4. 用語集 (Glossary)

本プロジェクトで使用する主要な用語を定義する。

- **CIF (Customer Information File)**: 顧客情報ファイル。顧客IDをキーとして全取引・契約情報を紐付けるマスタ。
- **KYC (Know Your Customer)**: 本人確認手続き。犯罪収益移転防止法に基づく本人特定事項の確認。
- **AML (Anti-Money Laundering)**: マネーロンダリング対策。疑わしい取引の届出など。
- **RTGS (Real-Time Gross Settlement)**: 即時グロス決済。日本銀行金融ネットワークシステム（日銀ネット）などで行われる決済方式。
- **ACID**: データベーストランザクションの4特性（Atomicity, Consistency, Isolation, Durability）。
- **2PC (Two-Phase Commit)**: 2相コミット。分散トランザクションの整合性を保証するプロトコル。
- **Saga**: マイクロサービスにおける分散トランザクション管理パターン。
- **HSM (Hardware Security Module)**: 耐タンパー性を備えたセキュリティモジュール。鍵管理に使用。
- **SWIFT**: 国際銀行間通信協会。海外送金メッセージの標準フォーマット。
- **全銀システム (Zengin System)**: 全国銀行データ通信システム。国内の為替取引を担う。
- **Basel III**: 国際統一基準（バーゼル規制）。自己資本比率規制など。
- **FATCA**: 米国の外国口座税務コンプライアンス法。
- **VaR (Value at Risk)**: リスク指標。
- **LCR (Liquidity Coverage Ratio)**: 流動性カバレッジ比率。

## 5. 次のステップ
Step 2 では、詳細なデータベース設計を行い、テーブル定義（DDL）を作成する。
