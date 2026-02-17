### ガチャAPI

#### POST /api/v1/gacha/pull
**説明**: ガチャを実行する

**リクエストヘッダ**:
| ヘッダ | 必須 | 説明 |
|---|---|---|
| Authorization | ○ | Bearer {JWT} |
| X-Device-ID | ○ | デバイス識別子 |
| X-Request-ID | ○ | 冪等性キー (UUID) |

**リクエストボディ**:
```json
{
  "banner_id": 123,
  "pull_type": "single|multi",
  "use_ticket": false
}
```

**レスポンス 200**:
```json
{
  "results": [
    {
      "item_id": 456,
      "item_type": "character",
      "rarity": "SSR",
      "is_pickup": true,
      "is_pity": false,
      "animation_type": "ssr_pickup"
    }
  ],
  "remaining_currency": {
    "premium": 2700,
    "free": 0
  },
  "new_pity_count": 5,
  "transaction_id": "uuid-xxx"
}
```

**エラーレスポンス**:
| コード | 説明 |
|---|---|
| 400 | バナー終了済み・通貨不足 |
| 409 | 同一X-Request-IDで重複実行 |
| 503 | ガチャメンテナンス中 |

#### GET /api/v1/gacha/banners
**説明**: アクティブバナー一覧取得

**クエリパラメータ**:
| パラメータ | 型 | 説明 |
|---|---|---|
| type | string | フィルタ: normal/pickup/limited |
| include_ended | boolean | 終了バナー含む (default: false) |

#### GET /api/v1/gacha/history
**説明**: ガチャ履歴取得（90日分）

| パラメータ | 型 | 説明 |
|---|---|---|
| banner_id | int | バナーID絞り込み |
| page | int | ページ番号 (default: 1) |
| limit | int | 件数 (max: 100) |

### イベントAPI

#### GET /api/v1/events/active
**説明**: 開催中イベント一覧

#### POST /api/v1/events/{event_id}/play
**説明**: イベント参加・ポイント加算
```json
{
  "battle_result": "win|lose|draw",
  "score": 12500,
  "play_time_sec": 180
}
```

#### GET /api/v1/events/{event_id}/ranking
**説明**: イベントランキング
| パラメータ | 型 | 説明 |
|---|---|---|
| page | int | ページ |
| near_me | boolean | 自分の前後を取得 |

### 課金API

#### POST /api/v1/purchase/verify
**説明**: レシート検証・通貨付与
```json
{
  "platform": "ios|android",
  "product_id": "jp.example.game.stones.60",
  "transaction_id": "store-tx-id",
  "receipt_data": "base64-encoded-receipt"
}
```
