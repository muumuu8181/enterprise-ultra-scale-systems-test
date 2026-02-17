# 要件定義書 (REQUIREMENTS.md)

## 1. システム概要
本システムは、勘定系と情報系を統合した次世代の「銀行コアバンキングシステム」である。
高可用性、高スループット、スケーラビリティを備え、マイクロサービスアーキテクチャ（またはモジュラモノリスからマイクロサービスへの移行を前提とした構成）を採用する。

- **システム名**: 銀行コアバンキングシステム
- **最終目標コード量**: 250,000行以上

## 2. 非機能要件

### 2.1 性能要件
- **スループット**: 10,000 TPS (Transactions Per Second) 以上
- **レイテンシ**: 全APIレスポンス 1秒以内 (p99)

### 2.2 可用性
- **稼働率**: 99.999% (年間ダウンタイム 5分以内)
- **RPO (Recovery Point Objective)**: 0秒 (データロストなし)
- **RTO (Recovery Time Objective)**: 1分以内

### 2.3 セキュリティ
- **認証**: OAuth2.0 + OIDC, MFA (TOTP)
- **暗号化**: 通信(TLS 1.3), 保存データ(AES-256-GCM), 鍵管理(HSM連携想定)
- **監査**: 全操作ログの7年間保存, 改ざん検知(ハッシュチェーン)

## 3. 技術スタック

### 3.1 アプリケーション
- **言語**: Python 3.11+
- **フレームワーク**: FastAPI (非同期処理)
- **ORM**: SQLAlchemy 2.0 (Async)

### 3.2 データベース・ストレージ
- **RDBMS**: PostgreSQL 15
    - パーティショニング (TimescaleDB / Native)
    - ストリーミングレプリケーション (Sync/Async)
- **キャッシュ**: Redis 7.x (Cluster mode)

### 3.3 メッセージング・非同期処理
- **メッセージブローカー**: Apache Kafka 3.x
    - イベント駆動アーキテクチャ (Event Sourcing / CQRS)
    - ログ圧縮 (Log Compaction)

### 3.4 インフラ・コンテナ
- **コンテナランタイム**: Docker
- **オーケストレーション**: Kubernetes (K8s)
- **CI/CD**: GitHub Actions / Jenkins

## 4. 用語集 (Glossary)

| 用語 | 英語 | 説明 |
| :--- | :--- | :--- |
| **CIF** | Customer Information File | 顧客情報ファイル。顧客の基本属性や取引履歴を一元管理する。 |
| **KYC** | Know Your Customer | 本人確認。口座開設時や高額取引時に行われる顧客の身元確認プロセス。 |
| **AML** | Anti-Money Laundering | マネーロンダリング対策。不正資金の移動を検知・防止する仕組み。 |
| **RTGS** | Real-Time Gross Settlement | 即時グロス決済。銀行間の資金決済を1件ごとに即時に行う方式。日銀ネット等。 |
| **ACID** | Atomicity, Consistency, Isolation, Durability | トランザクション処理に求められる4つの特性（原子性、一貫性、分離性、永続性）。 |
| **2PC** | Two-Phase Commit | 2相コミット。分散データベース間でトランザクションの整合性を保つプロトコル。 |
| **Saga** | Saga Pattern | 分散トランザクションパターン。各サービスでのローカルトランザクションを連鎖させ、失敗時は補償トランザクションを実行する。 |
| **HSM** | Hardware Security Module | ハードウェアセキュリティモジュール。暗号鍵の生成・保管・処理を安全に行う専用ハードウェア。 |
| **SWIFT** | Society for Worldwide Interbank Financial Telecommunication | 国際銀行間通信協会。国際送金などの金融メッセージをやり取りするネットワーク。 |
| **全銀** | Zengin System | 全国銀行データ通信システム。日本の金融機関間の内国為替取引を中継するシステム。 |
| **Basel III** | Basel III | 国際的な銀行規制フレームワーク。自己資本比率や流動性比率などの規制。 |
| **FATCA** | Foreign Account Tax Compliance Act | 外国口座税務コンプライアンス法。米国納税義務者の海外口座情報を収集するための米国の法律。 |
| **VaR** | Value at Risk | 市場リスク指標。特定の期間・確率における最大損失予想額。 |
| **LCR** | Liquidity Coverage Ratio | 流動性カバレッジ比率。短期的な資金流出に対する流動性資産の保有比率。 |
