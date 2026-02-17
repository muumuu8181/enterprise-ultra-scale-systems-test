### ガチャシステムテストケース

| テストID | カテゴリ | シナリオ | 事前条件 | 操作 | 期待結果 |
|---|---|---|---|---|---|
| TC-GACHA-001 | 正常系 | 単発ガチャ実行（有償石） | 有償石300個所持 | POST /gacha/pull {pull_type: "single"} | アイテム1個取得、有償石300消費、pity+1 |
| TC-GACHA-002 | 正常系 | 10連ガチャ実行 | 有償石3000個所持 | POST /gacha/pull {pull_type: "multi"} | アイテム10個取得、3000消費、SR1枚確定 |
| TC-GACHA-003 | 正常系 | 天井到達でSSR確定 | pity_count=99 | POST /gacha/pull {pull_type: "single"} | SSRアイテム取得、is_pity=true、pityリセット |
| TC-GACHA-004 | 正常系 | ソフト天井（75連以降確率UP） | pity_count=75 | 連続ガチャ実行 | SSR排出率が通常の2倍以上 |
| TC-GACHA-005 | 異常系 | 通貨不足 | 有償石200個所持 | POST /gacha/pull {pull_type: "single"} | HTTP 400, error_code: INSUFFICIENT_CURRENCY |
| TC-GACHA-006 | 異常系 | 終了バナーへのアクセス | バナー終了後 | POST /gacha/pull | HTTP 400, error_code: BANNER_EXPIRED |
| TC-GACHA-007 | 冪等性 | 同一Request-IDで2回実行 | 正常な通貨所持 | 同一X-Request-IDで2回POST | 2回目は同じレスポンスを返す（二重消費なし） |
| TC-GACHA-008 | 同時実行 | 同一ユーザーが100ms間隔で連打 | 正常状態 | 並列10リクエスト | 通貨が正確に消費（楽観的ロックで整合性保証） |

### 課金テストケース

| テストID | カテゴリ | シナリオ | 期待結果 |
|---|---|---|---|
| TC-PAY-001 | 正常系 | iOSレシート検証成功 | 石付与、purchase_id生成 |
| TC-PAY-002 | 正常系 | Androidレシート検証成功 | 同上 |
| TC-PAY-003 | 異常系 | 不正レシート | HTTP 400, 石付与なし |
| TC-PAY-004 | 異常系 | 重複レシート | HTTP 409, 二重付与なし |
| TC-PAY-005 | 異常系 | レシート検証APIタイムアウト | リトライ3回後、pendingに保留 |

### イベントテストケース

| テストID | カテゴリ | シナリオ | 期待結果 |
|---|---|---|---|
| TC-EVT-001 | 正常系 | イベント参加・ポイント加算 | points更新、ランキング反映（<1sec） |
| TC-EVT-002 | 正常系 | ランキング1000万人規模 | TOP100取得<100ms |
| TC-EVT-003 | 異常系 | 終了後にポイント加算 | HTTP 400, EVENT_ENDED |
| TC-EVT-004 | 負荷 | イベント開始時同時アクセス10万人 | エラーなし、キュー処理 |
