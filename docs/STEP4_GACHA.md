# Step 4: ガチャエンジン仕様

## 1. 概要
ガチャエンジンは、確率に基づいたアイテムの抽選を行うシステムの中核である。
公平性と信頼性が最も重要であり、全ての抽選結果は監査可能でなければならない。
**Python `secrets` モジュール (CSPRNG)** を使用し、暗号論的に安全な乱数生成を行う。

## 2. 確率・抽選ロジック (`GachaEngine`)

### 2.1 排出確率設定
- **N:** 68.0%
- **R:** 25.0%
- **SR:** 6.0%
- **SSR:** 1.0%

### 2.2 ピックアップ補正 (Pickup Rate Up)
- 特定のキャラクターの排出率を上昇させる。
- SSR枠 (1.0%) のうち、**50% (0.5%)** をピックアップ対象とする。
- 残りの **50% (0.5%)** は恒常SSRから均等割。

### 2.3 天井システム (Pity System)
`src/core/gacha/pity.py`

- **ハード天井 (Hard Pity):**
  - ガチャを **100回** 引いてSSRが出なかった場合、次回 (101回目) は **SSR確定** とする。
  - SSR排出時にカウントは **0** にリセットされる。

- **ソフト天井 (Soft Pity - Optional):**
  - **50回** 以降、SSR確率が徐々に上昇する (例: 1回ごとに +0.1%)。

- **天井カウントの独立性:**
  - `Normal Gacha` と `Limited Gacha A`, `Limited Gacha B` はそれぞれ別個に天井カウントを持つ。
  - 期間限定ガチャ終了時、カウントはリセットされる (または「天井コイン」に変換)。

## 3. 抽選アルゴリズム
1. **レアリティ決定:**
   - 0.0 ~ 1.0 の乱数を生成 (`secrets.SystemRandom().random()`).
   - 累積確率と比較し、レアリティ (N/R/SR/SSR) を決定。
2. **アイテム決定:**
   - 決定したレアリティ内のアイテムリストを取得。
   - 各アイテムの重み (`weight`) に基づき、重み付き抽選 (`random.choices` like logic) を行う。
3. **ピックアップ判定:**
   - SSRの場合、ピックアップ対象か否かを判定 (50% check)。
4. **天井判定:**
   - 抽選前に現在の `pity_count` を確認。
   - `pity_count >= 100` ならば、強制的に SSR確定ロジックへ分岐。

## 4. トランザクション管理
ガチャ実行は、**課金通貨消費** と **アイテム付与**、**履歴保存** を含むため、厳密なトランザクション管理が必要。

```python
async def draw_gacha(player_id, gacha_id, count=10):
    async with db.transaction():
        # 1. 資産ロック & 消費 (SELECT FOR UPDATE)
        player_stats = await db.select_for_update(PlayerStats, player_id)
        if player_stats.gems < cost:
            raise InsufficientFundsError()
        player_stats.gems -= cost

        # 2. 抽選実行 (CPU bound)
        results = engine.draw(gacha_id, count)

        # 3. 履歴保存 (Partitioned Table)
        await db.bulk_insert(GachaHistory, results)

        # 4. アイテム付与
        await inventory_service.add_items(player_id, results)

        # 5. 天井更新
        await pity_manager.update(player_id, gacha_id, results)
```

## 5. ログ・監査
- 全ての抽選結果 (`gacha_histories`) は、プレイヤーID、ガチャID、日時、排出アイテム、消費コスト、**抽選時の天井カウント** を記録する。
- ユーザーからの問い合わせ ("確率がおかしい") に即座に回答できるよう、管理画面でログを検索可能にする。
