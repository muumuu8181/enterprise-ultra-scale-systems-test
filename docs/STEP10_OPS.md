# Step 10: 運用・性能テスト仕様 (STEP10_OPS.md)

## 1. 概要
本ドキュメントは、システムのリリース後の運用手順（Runbook）および、非機能要件を満たすための性能テスト戦略を定義する。

## 2. 性能テスト仕様 (`tests/performance/`)

`Locust` を用いた分散負荷テストを実施し、目標TPS（10,000 TPS）とレイテンシ（p99 < 1s）の達成を確認する。

### 2.1 シナリオ定義 (`locustfile.py`)

#### Class: DepositUser
- **Weight**: 30%
- **Behavior**:
  - `/api/transactions/deposit` を呼び出す。
  - ランダムな金額を入金する。
  - 成功応答（200 OK）を確認する。
  - **目標**: 3,000 RPS

#### Class: TransferUser
- **Weight**: 20%
- **Behavior**:
  - `/api/transactions/transfer` を呼び出す。
  - 事前に用意された口座ペア間で送金を行う。
  - **目標**: 2,000 RPS

#### Class: BalanceUser
- **Weight**: 50%
- **Behavior**:
  - `/api/accounts/{id}/balance` を呼び出す。
  - 残高照会（Read-heavy workload）。
  - **目標**: 5,000 RPS

### 2.2 実施基準 (Pass Criteria)

| 指標 | 基準値 | 備考 |
| :--- | :--- | :--- |
| **Throughput** | 10,000 TPS 以上 | 全シナリオ合計 |
| **Latency (p95)** | 500 ms 未満 | |
| **Latency (p99)** | 1,000 ms 未満 | スパイク時も許容 |
| **Error Rate** | 0.1% 未満 | バリデーションエラーを除くシステムエラー |
| **Resource Usage** | CPU < 70%, Mem < 80% | DBおよびAppサーバー |

## 3. 運用ドキュメント (`docs/operations/`)

### 3.1 定常運用 (`RUNBOOK.md`)

#### 日次業務 (Daily)
- **09:00**: オンラインサービス開始確認（Health Check API）
- **15:00**: 全銀システム・SWIFT 締め処理確認
- **23:55**: オンラインサービス一時停止（または縮退運転）
- **00:00**: バッチジョブ実行開始
  - 利息計算 (`interest_calc_batch`)
  - 勘定照合・残高試算 (`reconciliation_batch`)
  - ログローテーション・アーカイブ

#### 週次・月次業務
- **週次**: DBフルバックアップ取得（日曜深夜）
- **月次**: 月次決算処理、監査ログのハッシュチェーン検証、長期保管ストレージへの退避

### 3.2 障害対応 (`INCIDENT_RESPONSE.md`)

#### Severity Levels
- **P1 (Critical)**: 全サービス停止、データ破損、大規模な金銭不整合。
  - 対応: 15分以内にSREチーム招集。CEO報告。
- **P2 (High)**: 一部機能停止（振込不可など）、大幅な遅延。
  - 対応: 1時間以内に調査開始。
- **P3 (Medium)**: 内部エラー多発、軽微なバグ。
  - 対応: 翌営業日対応可。

#### 対応フロー
1. **検知**: Prometheus Alertmanager / Datadog からのアラート。
2. **一次切り分け**: エラーログ確認、リソース状況確認。
3. **暫定対処**: 不正なPodの再起動、サーキットブレーカー発動、リードレプリカへの切り替え。
4. **恒久対処**: コード修正、設定変更、パッチ適用。
5. **事後分析 (Post-Mortem)**: 原因究明、再発防止策策定。

### 3.3 バックアップ・リストア (`BACKUP_RESTORE.md`)

- **PostgreSQL**:
  - `pg_backrest` または AWS RDS Snapshot を使用。
  - **PITR (Point-in-Time Recovery)**: WALアーカイブを用いて、障害発生直前（RPO=0に近い状態）まで復旧可能にする。
- **定期訓練**:
  - 四半期に1回、本番データ（マスキング済み）を用いたリストア訓練を実施し、RTO（目標1時間）を計測する。

### 3.4 監視ルール (`MONITORING.md`)

Prometheus / Grafana ダッシュボードで監視する主要メトリクス。

- **App**: Request Rate, Error Rate, Latency (Golden Signals)
- **DB**: Connection Pool Usage, Lock Wait Time, Deadlock Count, Replication Lag
- **Infra**: CPU Load, Memory Usage, Disk I/O, Network Traffic
