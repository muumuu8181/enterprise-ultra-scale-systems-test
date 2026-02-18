# Step 4: 取引処理モジュール仕様 (STEP4_TRANSACTION.md)

## 1. 概要
本ドキュメントは、入金、出金、振込といった勘定系の中核となる取引処理（Transaction Processing）の仕様を定義する。
データの整合性（ACID特性）を厳密に保証する必要がある。

## 2. トランザクション管理モジュール (`src/core/transaction/`)

### 2.1 データモデル (`models.py`)

#### Class: Transaction
- **Fields**:
  - `transaction_id`: UUID
  - `account_id`: UUID
  - `amount`: Decimal
  - `type`: TransactionType
  - `status`: TransactionStatus
  - `description`: str
  - `created_at`: datetime

#### Enum: TransactionType
- `DEPOSIT`: 入金
- `WITHDRAWAL`: 出金
- `TRANSFER_IN`: 振込入金
- `TRANSFER_OUT`: 振込出金
- `INTEREST`: 利息入金
- `FEE`: 手数料引落

#### Enum: TransactionStatus
- `PENDING`: 処理中
- `COMPLETED`: 完了
- `FAILED`: 失敗
- `REVERSED`: 取消（組戻し等）

### 2.2 リポジトリ (`repository.py`)

#### Class: TransactionRepository

- `insert(tx: Transaction) -> Transaction`
  - 取引履歴を新規作成する。
- `find_by_id(tx_id: UUID) -> Optional[Transaction]`
  - IDで検索する。
- `find_by_account(account_id, from_date, to_date, page, size) -> Page[Transaction]`
  - 指定口座の取引明細を期間指定で取得する。
- `find_pending(account_id) -> List[Transaction]`
  - 処理中ステータスの取引を取得する。
- `update_status(tx_id, status) -> Transaction`
  - ステータスを更新する。
- `sum_by_type_today(account_id, tx_type) -> Decimal`
  - 当日の指定種別の取引合計額を取得する（日次限度額チェック用）。

### 2.3 入金サービス (`deposit_service.py`)

#### Class: DepositService

- `deposit(account_id, amount, description, source_type) -> Transaction`
  - **概要**: 指定口座へ入金を行う。
  - **Source Type**: `ATM`, `COUNTER`, `TRANSFER`, `ONLINE`
  - **プロセス**:
    1. 入力値バリデーション（金額 > 0）。
    2. 口座状態チェック（`ACTIVE`であること）。
    3. `account.balance` を更新（`UPDATE accounts SET balance = balance + :amount ...`）。
    4. `transactions` テーブルにレコード挿入。
    5. 上記を同一のDBトランザクション内で実行。
    6. 監査ログを出力。

### 2.4 出金サービス (`withdrawal_service.py`)

#### Class: WithdrawalService

- `withdraw(account_id, amount, description, channel) -> Transaction`
  - **概要**: 指定口座から出金を行う。
  - **プロセス**:
    1. DBトランザクション開始。
    2. 口座レコードをロック（`SELECT FOR UPDATE`）。
    3. 残高チェック（`balance >= amount`）。不足時は `InsufficientFundsException`。
    4. 日次引出限度額チェック（LimitManager利用）。
    5. 口座凍結チェック。
    6. `account.balance` を更新（減算）。
    7. `transactions` テーブルにレコード挿入。
    8. コミット。

### 2.5 振込サービス (`transfer_service.py`)

#### Class: TransferService

- `transfer_internal(from_id, to_id, amount, description) -> TransferResult`
  - **概要**: 行内振込（即時決済）。
  - **デッドロック防止**:
    - `from_id` と `to_id` を比較し、IDが小さい順（昇順）にロックを取得する。
  - **プロセス**:
    1. 両口座をロック・検証。
    2. 出金処理（残高減算、履歴作成）。
    3. 入金処理（残高加算、履歴作成）。
    4. コミット。

- `transfer_external(from_id, to_bank_code, to_account_no, amount) -> TransferResult`
  - **概要**: 他行振込（全銀システム経由）。
  - **プロセス**:
    1. 出金元口座をロック・減算。
    2. 全銀フォーマットへの変換。
    3. 外部送金キュー（Kafka/Outbox）へメッセージ投入。
    4. コミット（ここまでが同期処理）。
    5. 非同期で全銀アダプタが送信処理を行う。

### 2.6 限度額管理 (`limit_manager.py`)

#### Class: LimitManager

- `check_daily_withdrawal_limit(account_id, amount) -> bool`
  - 本日の出金合計額 ＋ 今回の金額 が限度額内か判定。
- `check_monthly_transfer_limit(account_id, amount) -> bool`
  - 今月の振込合計額チェック。
- `get_remaining_daily_limit(account_id) -> Decimal`
  - 本日あといくら出金可能かを取得。
- `update_limit_usage(account_id, amount, tx_type) -> None`
  - Redis等を用いて高速に限度額使用状況を更新する（オプション、DB集計と併用）。
