# Step 10: 運用・パフォーマンス仕様

## 1. 概要
本システムの運用は、安定稼働と迅速な問題解決を目的とする。
24/365 のモニタリング体制を構築し、50,000 TPS の高負荷環境でもレスポンス目標を達成するための負荷テストを実施する。

## 2. モニタリング・アラート (`Prometheus` + `Grafana`)

### 2.1 監視メトリクス
- **API Request Rate:** エンドポイント別リクエスト数 (TPS)
- **Error Rate:** 5xx / 4xx エラー率 (0.01%以下目標)
- **Latency (P95/P99):** API応答時間 (200ms/500ms目標)
- **Gacha Hit Rate:** SSR排出率 (1.0% ± 0.1% 範囲内)
- **Billing Amount:** 売上推移 (急激な増減アラート)
- **Ranking Updates:** ランキング更新数
- **Redis Memory Usage:** キャッシュメモリ使用量

### 2.2 アラート通知 (`PagerDuty` / `Slack`)
- **Critical:** サービスダウン、課金エラー率 > 1%、SSR排出率異常
- **Warning:** レイテンシ悪化、DB CPU高負荷、ディスク容量低下

## 3. ログ収集・分析 (`ELK Stack` / `Fluentd`)

### 3.1 構造化ログ (JSON Log)
- 全てのアプリケーションログは JSON 形式で出力。
  ```json
  {"time": "...", "level": "INFO", "player_id": "...", "action": "DRAW_GACHA", "gacha_id": "...", "result": [...]}
  ```
- `Fluentd` で収集し、`Elasticsearch` に転送。
- `Kibana` でログ検索・可視化 (CS対応、調査用)。

### 3.2 監査証跡 (Audit Log)
- 課金、ガチャ、重要アイテム操作は `MongoDB` にも生ログとして保存。
- 改ざん検知のため、ハッシュチェーン等を検討。

## 4. 負荷テスト (`Locust`)

### 4.1 シナリオ設計 (`locustfile.py`)
- **Login Scenario:** ログイン -> プロフィール取得 (高頻度)
- **Gacha Scenario:** ガチャ画面 -> 10連ガチャ実行 -> 結果確認 (中頻度、重い処理)
- **Quest Scenario:** クエスト開始 -> 終了 -> 報酬獲得 (中頻度)
- **Event Scenario:** イベント画面 -> ランキング確認 -> スコア送信 (高頻度、Redis負荷)

### 4.2 目標値検証
- **User Count:** 10,000 users (Ramp up) -> 1,000,000 users (Peak)
- **Throughput:** 50,000 TPS (Gacha API specific)
- **Latency:** 95% < 200ms
- **Database CPU:** < 70% (at Peak)

### 4.3 ボトルネック対策
- **Slow Query:** `pg_stat_statements` で遅いクエリを特定し、インデックス追加やクエリ改善。
- **Connection Pool:** `PgBouncer` の設定チューニング (max_client_conn, default_pool_size)。
- **Redis Eviction:** メモリ不足時の挙動確認 (maxmemory-policy: allkeys-lru)。

## 5. バックアップ・障害復旧 (DR)
- **DB Backup:** 毎日フルバックアップ (S3等へ転送)、WALアーカイブ (Point-in-Time Recovery対応)。
- **Redis Snapshot:** AOF (Append Only File) 有効化 (everysec)。
- **Failover Test:** 定期的に DB/Redis のマスター障害発生訓練を実施。
