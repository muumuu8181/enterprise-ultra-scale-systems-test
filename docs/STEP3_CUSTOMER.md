# Step 3: 顧客・口座管理モジュール仕様 (STEP3_CUSTOMER.md)

## 1. 概要
本ドキュメントは、顧客管理（CIF）および口座管理（Ledger）のコアモジュール仕様を定義する。
これらのモジュールは、システムの中で最も基本的かつ重要なドメインロジックを含む。

## 2. 顧客管理モジュール (`src/core/customer/`)

顧客の登録、KYC（本人確認）、リスク評価を管理する。

### 2.1 データモデル (`models.py`)

#### Class: Customer
顧客の基本属性を表現するモデル。
- **Fields**:
  - `customer_id`: UUID
  - `name`: str
  - `address`: str
  - `tax_id`: str
  - `kyc_status`: KycStatus
  - `created_at`: datetime

#### Class: CustomerContact
連絡先情報。
- **Fields**:
  - `email`: str
  - `phone`: str
  - `address_type`: str

#### Class: CustomerDocument
KYC書類。
- **Fields**:
  - `doc_type`: str
  - `doc_number`: str
  - `expiry_date`: date

#### Enum: KycStatus
- `PENDING`: 確認待ち
- `VERIFIED`: 確認済み
- `REJECTED`: 却下
- `EXPIRED`: 期限切れ

#### Enum: RiskLevel
- `LOW`: 低リスク
- `MEDIUM`: 中リスク
- `HIGH`: 高リスク（要監視）
- `BLOCKED`: 取引停止

### 2.2 リポジトリ (`repository.py`)

#### Class: CustomerRepository
DBアクセスを抽象化する。

- `create(customer: Customer) -> Customer`
  - 新規顧客を保存する。
- `find_by_id(customer_id: UUID) -> Optional[Customer]`
  - IDで検索する。
- `find_by_tax_id(tax_id: str) -> Optional[Customer]`
  - マイナンバー等で重複チェックを行う。
- `search(name: str, page: int, size: int) -> Page[Customer]`
  - 名前で部分一致検索を行う。
- `update_kyc_status(customer_id, status) -> Customer`
  - KYCステータスを更新する。
- `update_risk_score(customer_id, score) -> Customer`
  - リスクスコアを更新する。
- `soft_delete(customer_id) -> None`
  - 顧客を論理削除する。

### 2.3 サービス (`service.py`)

ビジネスロジックを実装する。

#### Class: CustomerService

- `register(dto: CustomerRegistrationDto) -> Customer`
  - 顧客登録フロー。バリデーション、重複チェックを行い、リポジトリを呼び出す。
- `verify_kyc(customer_id, documents) -> KycResult`
  - KYC書類を確認し、ステータスを更新する（外部KYCプロバイダ連携想定）。
- `update_contact(customer_id, contact_dto) -> CustomerContact`
  - 連絡先を更新し、変更履歴を監査ログに残す。
- `get_risk_profile(customer_id) -> RiskProfile`
  - 現在のリスクスコアと属性を取得する。
- `check_aml_flag(customer_id) -> bool`
  - AMLフラグが立っているか確認する。

## 3. 口座管理モジュール (`src/core/account/`)

口座の開設、解約、残高管理を行う。

### 3.1 データモデル (`models.py`)

#### Class: Account
- **Fields**:
  - `account_id`: UUID
  - `customer_id`: UUID
  - `account_type`: AccountType
  - `balance`: Decimal
  - `status`: AccountStatus

#### Enum: AccountType
- `SAVINGS`: 普通預金
- `CURRENT`: 当座預金
- `TIME_DEPOSIT`: 定期預金
- `ORDINARY`: 通常貯金

#### Enum: AccountStatus
- `ACTIVE`: 有効
- `FROZEN`: 凍結（不正疑い等）
- `CLOSED`: 解約済み
- `DORMANT`: 休眠

### 3.2 リポジトリ (`repository.py`)

#### Class: AccountRepository

- `create(account: Account) -> Account`
  - 新規口座を作成する。
- `find_by_id(account_id: UUID) -> Optional[Account]`
  - IDで検索する。
- `find_by_customer_id(customer_id) -> List[Account]`
  - 顧客に紐づく口座一覧を取得する。
- `update_balance(account_id, amount, lock=True) -> Account`
  - 残高を更新する。`SELECT FOR UPDATE` による排他制御が必須。
- `update_status(account_id, status) -> Account`
  - 口座ステータスを変更する。
- `get_balance_with_lock(account_id) -> Decimal`
  - 悲観的ロックを取得して現在の残高を取得する。

### 3.3 サービス (`service.py`)

#### Class: AccountService

- `open_account(customer_id, account_type) -> Account`
  - 新規口座開設。顧客ステータスチェック（KYC済みか）を含む。
- `close_account(account_id) -> None`
  - 口座解約。残高がゼロであること、未決済取引がないことを確認する。
- `freeze_account(account_id, reason) -> None`
  - 口座凍結。入出金を停止する。
- `get_balance(account_id) -> Decimal`
  - 現在高照会。
- `get_statement(account_id, from_date, to_date, page, size) -> Page[Transaction]`
  - 取引明細を取得する（Transaction Serviceへ委譲）。

### 3.4 利息計算 (`interest.py`)

#### Class: InterestCalculator

- `calculate_daily_interest(account: Account, date: date) -> Decimal`
  - 日次利息計算（残高 × 日歩）。
- `calculate_compound_interest(principal, rate, days) -> Decimal`
  - 複利計算ロジック。
- `calculate_withholding_tax(interest: Decimal) -> Decimal`
  - 源泉分離課税（20.315%）を計算する。

#### Class: InterestBatchProcessor

- `run_daily_batch(target_date: date) -> BatchResult`
  - 全口座に対して日次利息計算を実行するバッチエントリポイント。
- `process_account(account_id, date) -> InterestRecord`
  - 個別口座の利息計算処理。
- `post_interest_to_account(account_id, interest) -> Transaction`
  - 計算された利息を入金トランザクションとして記録する（決算日のみ）。
