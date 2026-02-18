# Step 5: ライブイベント管理仕様

## 1. 概要
ライブイベントは、プレイヤーのエンゲージメントを高めるための期間限定コンテンツである。
ランキング形式、ポイント報酬形式、ストーリー形式など多様なイベントタイプに対応し、
開始・終了・集計・報酬配布までのライフサイクルを管理する。

## 2. イベントライフサイクル (`EventScheduler`)
`src/core/event/scheduler.py`

### 2.1 ステータス遷移
1. **Planned (予定):** マスタ登録済みだが開始前。告知バナーのみ表示。
2. **Active (開催中):** プレイ可能、スコア加算有効。
3. **Closing (集計中):** プレイ不可。ランキング最終確定処理中。
4. **Finished (終了):** 結果発表、報酬受取可能。
5. **Archived (アーカイブ):** 表示終了。

### 2.2 スケジューリング
- `APScheduler` (Python) を使用し、毎分チェックを行う。
- `start_at` 到来時に `is_active=True` に更新、キャッシュ (Redis) にイベント情報をロード。
- `end_at` 到来時に `is_active=False` に更新、集計ジョブをキック。

## 3. スコア・ランキングロジック (`RankingIntegration`)

### 3.1 スコア加算
- プレイヤーがクエスト/バトルクリア時に `submit_score(event_id, score)` を呼び出す。
- バリデーション (異常値チェック) 後、Redis (Ranking Service) に `ZADD` コマンドで書き込み。
- 同時に `event_participations` テーブルの `score` も更新 (永続化)。

### 3.2 報酬配布 (`RewardDistributor`)
- **ポイント達成報酬:**
  - スコア更新時に閾値チェックを行い、未受取の報酬があれば即時付与。
  - `event_rewards` テーブル参照。

- **ランキング報酬:**
  - イベント終了後、バッチ処理でランキング確定 (`ZREVRANGE 0 -1 WITHSCORES`)。
  - 上位○% または ○位以内 の条件に基づき、報酬アイテムを `present_box` (Mail) に送付。

## 4. イベントタイプ詳細

### 4.1 ランキングイベント (Ranking Event)
- 期間内の最高スコアまたは累計スコアを競う。
- Redis Sorted Sets の `ZADD` / `ZINCRBY` を使い分ける。

### 4.2 レイドイベント (Raid Event)
- 全プレイヤー協力型。
- ボスHPを Redis (`DECRBY`) で共有管理。
- 討伐成功時に全員に報酬配布。

### 4.3 ボックスガチャイベント (Box Gacha)
- イベント専用チケットで「ボックスガチャ」を引く。
- 箱の中身 (在庫数) は Redis Hash で管理 (`HINCRBY`)。
- `gacha_engine` を流用しつつ、在庫減算ロジックを追加。
