# Step 8: ランキング・スコアボード仕様

## 1. 概要
ランキングサービスは、50,000 TPS の更新リクエストと 50ms 以内のレイテンシを実現するため、
Python (FastAPI) ではなく **Go言語 (Golang)** で実装されたマイクロサービスとする。
Redis Sorted Sets を活用し、イベント終了時のスナップショット作成機能も提供する。

## 2. アーキテクチャ

### 2.1 コンポーネント
- **Go Ranking Service:** gRPC / HTTP サーバー
- **Redis Cluster:** シャーディング構成 (3 Master / 3 Replica)
- **FastAPI (Client):** プレイヤーからのスコア送信を受け、gRPC で Go Service に転送

### 2.2 Go 実装詳細 (`ranking/service.go`)

- **Interface Definition (Proto):**
  ```protobuf
  service RankingService {
      rpc UpdateScore(UpdateScoreRequest) returns (UpdateScoreResponse);
      rpc GetRank(GetRankRequest) returns (GetRankResponse);
      rpc GetTopN(GetTopNRequest) returns (GetTopNResponse);
      rpc GetAroundPlayer(GetAroundPlayerRequest) returns (GetAroundPlayerResponse);
  }
  ```

- **UpdateScore:**
  - Redis `ZADD` (スコア更新) または `ZINCRBY` (加算) を実行。
  - **Pipeline** を使用してバッチ処理を行い、Redis へのラウンドトリップを削減。
  - 同時書き込み競合は Redis のシングルスレッド特性により回避。

- **GetRank:**
  - Redis `ZREVRANK` (降順ランク取得)。
  - `ZSCORE` も同時に取得し、順位とスコアを返す。

- **GetTopN:**
  - Redis `ZREVRANGE 0 N WITHSCORES` (上位取得)。
  - キャッシュ層 (Go In-Memory Cache) を併用し、Redis 負荷をさらに低減 (TTL 1秒程度)。

- **GetAroundPlayer:**
  - `ZREVRANK` で自身の順位取得後、`ZREVRANGE` で前後 10件を取得。

## 3. スナップショットと永続化 (`SnapshotWorker`)

### 3.1 定期バックアップ
- Redis は揮発性メモリのため、障害時にデータ消失リスクがある (AOF/RDB はあるが完全ではない)。
- 1分ごとに `ZREVRANGE 0 -1 WITHSCORES` で全データを取得し、
  Go Service が PostgreSQL の `event_rankings` テーブルにバルクインサート (`COPY` コマンド)。

### 3.2 イベント終了時確定
- イベント終了時刻 (`end_at`) 到来後、Go Service が最終ランキング確定ジョブを実行。
- Redis のデータを全て取得し、DBに保存 (`status='final'`)。
- 報酬配布バッチがこの確定データを参照してメール送信を行う。

## 4. パーティショニング戦略
- **Leaderboard Key Design:**
  - `lb:{event_id}:{group_id}`
  - イベント参加者が 100万人を超える場合、単一キーでは Redis インスタンスのメモリ限界や CPU ボトルネックになる可能性がある。
  - ユーザーIDハッシュなどで 10〜100 のグループ (`group_id`) に分割し、
    各グループ内でランキング集計 -> 最終的にマージソートして総合ランキング算出、またはグループ別ランキングとして扱う。
