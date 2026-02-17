# Step 7: 課金・決済・レシート検証仕様

## 1. 概要
課金モジュールは、アプリストア (App Store, Google Play) 経由の購入処理を安全に管理し、不正なレシートによる資産獲得を防ぐ。
最も重要な要件は、**冪等性 (Idempotency)** の確保と **PCI DSS 準拠 (カード情報非保持)** である。

## 2. 決済フロー (`BillingService`)

1. **購入開始 (Client -> Server):**
   - `initiate_purchase(product_id)` を呼び出し、サーバー側でトランザクションID (UUID) を発行。
   - ストアSDK (StoreKit / Billing Library) にこのIDを渡して決済を開始。

2. **決済完了 & レシート送信 (Client -> Server):**
   - ストア側で購入完了後、レシートデータ (Base64) を受け取る。
   - `verify_purchase(receipt_data, transaction_id)` を呼び出す。

3. **レシート検証 (Server -> Store API):**
   - `Apple Verify Receipt API` (Production/Sandbox) または `Google Play Android Developer API` に問い合わせ。
   - レシートの真正性 (`status=0` or `purchaseState=0`) を確認。
   - `transaction_id` (original_transaction_id) の重複チェック (Replay Attack防止)。

4. **アイテム付与 (Server Internal):**
   - 検証成功時、`purchases` テーブルにレコード作成 (ステータス: `verified`)。
   - `inventory_service.add_items` または `player_service.add_gems` を呼び出す。
   - 完了後、ステータスを `completed` に更新。

## 3. レシート検証詳細 (`ReceiptVerifier`)

### 3.1 Apple (App Store)
- **Endpoint:** `https://buy.itunes.apple.com/verifyReceipt` (本番)
- **Payload:** `{"receipt-data": "BASE64_STRING", "password": "SHARED_SECRET"}`
- **Response Check:**
  - `status`: 0 (正常)
  - `receipt.in_app`: 購入アイテムリスト
  - `original_transaction_id`: 重複チェックキー

### 3.2 Google (Play Store)
- **Library:** `google-api-python-client` (Service Account Key使用)
- **API:** `androidpublisher.purchases.products.get`
- **Params:** `packageName`, `productId`, `token`
- **Response Check:**
  - `purchaseState`: 0 (購入済み)
  - `consumptionState`: 0 (未消費) -> 1 (消費済み) に更新する必要あり

## 4. 冪等性と障害対策

- **重複実行防止:**
  - `purchases` テーブルの `transaction_id` カラムにユニーク制約 (Unique Constraint) を設定。
  - 同一レシートが再送された場合、DBレベルでエラー (IntegrityError) とし、既に付与済みであることを返す。

- **トランザクション:**
  - `purchase` 作成と `add_gems` は同一DBトランザクションで実行。
  - 途中で失敗した場合、ロールバックされ、レシートは未処理状態 (Pending) に戻る。
  - クライアントはリトライ可能。

## 5. 返金・キャンセル処理
- ストア側で返金が行われた場合、Apple/Google から **Server-to-Server Notification (Webhook)** を受け取る。
- 返金通知 (`REFUND` event) を検知したら、対象ユーザーの有償石を減算 (マイナスも許容) またはアカウントBANを検討する。
- `billing_refunds` テーブルに履歴を保存。
