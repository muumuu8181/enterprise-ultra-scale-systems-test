# Step 6: インベントリ・アイテム管理仕様

## 1. 概要
インベントリ管理は、ゲーム内のアイテム獲得、消費、強化、合成、所持上限管理を司る。
アイテムの増減は全てDBのトランザクション内でアトミックに行い、不正な増殖や消失を防ぐ。

## 2. アイテム設計 (`ItemModel`)
`src/core/inventory/models.py`

- **ItemType:**
  - `character`: キャラクターカード (スタック不可)
  - `weapon`: 武器・装備 (スタック不可、レベル・ステータスを持つ)
  - `material`: 強化素材 (スタック可能: Max 999)
  - `currency`: 通貨・石 (player_statsで管理するためinventory外)
  - `costume`: キャラクタースキン (スタック不可、1個限定)

- **ItemRarity:** `N`, `R`, `SR`, `SSR`
- **UniqueConstraint:** `player_id`, `item_id`, `enhancement_level` (スタック可能な場合)

## 3. インベントリサービス (`InventoryService`)
`src/core/inventory/service.py`

### 3.1 アイテム操作

| メソッド名 | 説明 | 備考 |
| :--- | :--- | :--- |
| `add_items(player_id, items: List[ItemGrant])` | 複数アイテム付与 | スタック上限チェック、倉庫行き判定 |
| `consume_items(player_id, items: List[ItemConsume])` | 複数アイテム消費 | 在庫不足時は例外スロー (Atomic) |
| `lock_item(player_id, inventory_id, locked)` | ロック状態変更 | 誤売却・誤合成防止 |
| `expand_inventory(player_id, count)` | 倉庫枠拡張 | 石消費 |

### 3.2 強化・合成 (`EnhancementService`)
`src/core/inventory/enhancement.py`

- **強化ロジック:**
  - `base_item` (強化元) + `materials` (素材) -> `enhanced_item` (結果)
  - 成功確率判定 (乱数)
  - 大成功/超大成功ボーナス (経験値1.5倍/2.0倍)
  - コイン消費計算: `base_rarity * material_count * 100`

- **限界突破:**
  - 同一アイテム合成によるレベル上限開放
  - スキルレベルアップ確率計算

## 4. データ整合性
- **楽観的ロック (Optimistic Locking):**
  - `player_inventory` の更新時に `version` カラムまたは `updated_at` を使用し、同時更新による不整合を防止。
  - `UPDATE player_inventory SET quantity = quantity - 1 WHERE id = ... AND quantity >= 1`

- **非同期処理:**
  - 大量アイテム配布 (全プレ) は Kafka 経由で非同期バッチ処理として実行し、APIレスポンス遅延を防ぐ。
