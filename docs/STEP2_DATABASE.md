# Step 2: データベース詳細設計 (STEP2_DATABASE.md)

## 1. 概要
本ドキュメントは、銀行コアバンキングシステムのデータベーススキーマ詳細を定義する。
全テーブルに対して共通のカラム定義、インデックス戦略、パーティショニング戦略を適用する。

## 2. 共通仕様

### 2.1 カラム定義
- **ID**: `UUID` (v4) または `BIGSERIAL` を主キーとする。
- **日時**: `TIMESTAMPTZ` (UTC) を使用。
- **金額**: `DECIMAL(19,4)` を使用（浮動小数点型は禁止）。
- **監査用カラム**: 全テーブルに以下を付与する。
  - `created_at TIMESTAMPTZ DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ DEFAULT NOW()`

### 2.2 インデックス戦略
- 主キー (PK)
- 外部キー (FK)
- 検索頻度の高いカラム (`customer_id`, `account_id`, `created_at`, `status`)
- 部分インデックス (Partial Index) を活用し、Activeなレコードへのアクセスを高速化する。

### 2.3 パーティショニング
- `transactions`: `created_at` による月次レンジパーティション
- `audit_logs`: `created_at` による月次レンジパーティション

**注意**: PostgreSQLのネイティブパーティショニングを使用する場合、外部キー制約の参照元・参照先に制約がある。
パーティション化されたテーブル（`transactions`など）を参照する外部キーを作成する場合や、パーティション化されたテーブルから他のテーブルを参照する場合の考慮が必要である。
本設計では論理的な関係性を示すためにFKを記載しているが、実装時にはトリガーによる整合性チェックやアプリケーション側での制御が必要になる場合がある。

## 3. DDL一覧

### 3.1 顧客系 (Customer Domain)

#### customers
顧客の基本情報を管理する。CIFの中核テーブル。
```sql
CREATE TABLE customers (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    tax_id VARCHAR(50) UNIQUE, -- マイナンバー等
    kyc_status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, VERIFIED, REJECTED
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_customers_tax_id ON customers(tax_id);
```

#### customer_contacts
顧客の連絡先情報を管理する。
```sql
CREATE TABLE customer_contacts (
    contact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id),
    email VARCHAR(255),
    phone VARCHAR(50),
    address_type VARCHAR(20), -- HOME, OFFICE
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### customer_documents
KYCのための本人確認書類情報を管理する。
```sql
CREATE TABLE customer_documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id),
    doc_type VARCHAR(50), -- PASSPORT, DRIVER_LICENSE
    doc_number VARCHAR(100),
    expiry_date DATE,
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### customer_risk
AML/CFT観点でのリスク評価を管理する。
```sql
CREATE TABLE customer_risk (
    risk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id),
    risk_score INTEGER, -- 0-100
    aml_flag BOOLEAN DEFAULT FALSE,
    last_reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.2 口座系 (Account Domain)

#### accounts
顧客の口座を管理する。
```sql
CREATE TABLE accounts (
    account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id),
    account_type VARCHAR(20), -- SAVINGS, CURRENT, TIME_DEPOSIT
    currency VARCHAR(3) DEFAULT 'JPY',
    balance DECIMAL(19,4) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, FROZEN, CLOSED
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_accounts_customer ON accounts(customer_id);
```

#### account_types
口座種別の定義マスタ。
```sql
CREATE TABLE account_types (
    type_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### interest_rates
金利マスタ。適用日により履歴管理する。
```sql
CREATE TABLE interest_rates (
    rate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_type VARCHAR(20) REFERENCES account_types(type_code),
    rate DECIMAL(5,4), -- e.g. 0.0010 (0.1%)
    effective_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### account_limits
口座ごとの引出限度額設定。
```sql
CREATE TABLE account_limits (
    limit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(account_id),
    daily_limit DECIMAL(19,4),
    monthly_limit DECIMAL(19,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.3 取引系 (Transaction Domain)

#### transactions
全ての入出金取引を記録する。**月次パーティション対象**。
```sql
CREATE TABLE transactions (
    transaction_id UUID NOT NULL, -- PKの一部
    account_id UUID NOT NULL,
    amount DECIMAL(19,4) NOT NULL,
    type VARCHAR(20) NOT NULL, -- DEPOSIT, WITHDRAWAL, TRANSFER
    status VARCHAR(20) DEFAULT 'PENDING',
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (transaction_id, created_at) -- パーティションキーを含める
) PARTITION BY RANGE (created_at);
```

#### transaction_types
取引種別マスタ。
```sql
CREATE TABLE transaction_types (
    type_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50),
    is_credit BOOLEAN, -- 入金系か出金系か
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### transaction_details
取引の詳細情報（振込先口座情報など）。
```sql
CREATE TABLE transaction_details (
    detail_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID, -- Note: FK制約はパーティションテーブルに対して注意が必要
    counterparty_name VARCHAR(255),
    counterparty_bank_code VARCHAR(10),
    counterparty_account_no VARCHAR(20),
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### pending_transactions
2PCや長時間トランザクション（Saga）のための一時保管。
```sql
CREATE TABLE pending_transactions (
    pending_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    saga_id UUID,
    account_id UUID,
    amount DECIMAL(19,4),
    type VARCHAR(20),
    status VARCHAR(20), -- PREPARED, COMMITTING, ABORTING
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.4 為替・決済系 (Forex & Settlement Domain)

#### forex_transactions
外国為替取引履歴。
```sql
CREATE TABLE forex_transactions (
    forex_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID,
    from_currency VARCHAR(3),
    to_currency VARCHAR(3),
    rate DECIMAL(10,6),
    from_amount DECIMAL(19,4),
    to_amount DECIMAL(19,4),
    trade_date TIMESTAMPTZ,
    value_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### exchange_rates
為替レート履歴。
```sql
CREATE TABLE exchange_rates (
    rate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    currency_pair VARCHAR(7), -- USD/JPY
    rate DECIMAL(10,6),
    source VARCHAR(50), -- Reuters, Bloomberg
    effective_datetime TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### swift_messages
SWIFT電文ログ。
```sql
CREATE TABLE swift_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    direction VARCHAR(10), -- INBOUND, OUTBOUND
    mt_type VARCHAR(10), -- MT103, MT202
    sender_bic VARCHAR(11),
    receiver_bic VARCHAR(11),
    message_body TEXT,
    status VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### zengin_records
全銀システム電文ログ。
```sql
CREATE TABLE zengin_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    direction VARCHAR(10),
    format_type VARCHAR(20),
    data_body TEXT,
    status VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### settlements
決済管理マスタ。
```sql
CREATE TABLE settlements (
    settlement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    settlement_type VARCHAR(20), -- RTGS, NET
    status VARCHAR(20),
    settlement_date DATE,
    total_amount DECIMAL(19,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### rtgs_transactions
即時グロス決済取引。
```sql
CREATE TABLE rtgs_transactions (
    rtgs_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    settlement_id UUID REFERENCES settlements(settlement_id),
    from_bank_code VARCHAR(4),
    to_bank_code VARCHAR(4),
    amount DECIMAL(19,4),
    status VARCHAR(20), -- QUEUED, SETTLED, REJECTED
    settlement_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### net_positions
ネット決済ポジション。
```sql
CREATE TABLE net_positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    settlement_id UUID REFERENCES settlements(settlement_id),
    participant_id VARCHAR(10), -- BIC or Bank Code
    net_amount DECIMAL(19,4), -- Positive: Receivable, Negative: Payable
    status VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### payment_orders
支払指図。
```sql
CREATE TABLE payment_orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payer_account_id UUID REFERENCES accounts(account_id),
    payee_account_no VARCHAR(20),
    payee_bank_code VARCHAR(4),
    amount DECIMAL(19,4),
    due_date DATE,
    status VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.5 融資系 (Loan Domain)

#### loans
融資契約マスタ。
```sql
CREATE TABLE loans (
    loan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id),
    loan_type VARCHAR(20) REFERENCES loan_types(type_code),
    principal_amount DECIMAL(19,4),
    interest_rate DECIMAL(5,4),
    start_date DATE,
    maturity_date DATE,
    status VARCHAR(20), -- ACTIVE, PAID_OFF, DEFAULT
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### loan_types
融資種別マスタ。
```sql
CREATE TABLE loan_types (
    type_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    interest_rate_range_min DECIMAL(5,4),
    interest_rate_range_max DECIMAL(5,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### loan_applications
融資申込ワークフロー。
```sql
CREATE TABLE loan_applications (
    application_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id),
    loan_type VARCHAR(20) REFERENCES loan_types(type_code),
    amount DECIMAL(19,4),
    purpose TEXT,
    workflow_status VARCHAR(20), -- SUBMITTED, REVIEWING, APPROVED, REJECTED
    approver_id UUID,
    decision_date TIMESTAMPTZ,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### collaterals
担保情報マスタ。
```sql
CREATE TABLE collaterals (
    collateral_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID REFERENCES loans(loan_id),
    collateral_type VARCHAR(20), -- REAL_ESTATE, SECURITIES
    description TEXT,
    valuation DECIMAL(19,4),
    valuation_date DATE,
    lien_status VARCHAR(20), -- REGISTERED, RELEASED
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### repayment_schedules
返済予定表。
```sql
CREATE TABLE repayment_schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID REFERENCES loans(loan_id),
    due_date DATE,
    principal_amount DECIMAL(19,4),
    interest_amount DECIMAL(19,4),
    status VARCHAR(20), -- PENDING, PAID, OVERDUE
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### repayment_history
返済実績。
```sql
CREATE TABLE repayment_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID REFERENCES loans(loan_id),
    paid_date DATE,
    paid_amount DECIMAL(19,4),
    principal_portion DECIMAL(19,4),
    interest_portion DECIMAL(19,4),
    penalty_portion DECIMAL(19,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.6 セキュリティ・監査 (Security & Audit)

#### users / roles
管理ユーザーとロール。
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255),
    role VARCHAR(20),
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE roles (
    role_name VARCHAR(20) PRIMARY KEY,
    permissions JSONB, -- { "customer": ["read", "write"], ... }
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### audit_logs
監査ログ。**月次パーティション対象**。
```sql
CREATE TABLE audit_logs (
    log_id UUID NOT NULL,
    user_id UUID,
    action VARCHAR(50), -- UPDATE, DELETE, VIEW
    target_table VARCHAR(50),
    target_id VARCHAR(50),
    before_data JSONB,
    after_data JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (log_id, created_at)
) PARTITION BY RANGE (created_at);
```

#### access_logs
APIアクセスログ。
```sql
CREATE TABLE access_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    endpoint VARCHAR(255),
    method VARCHAR(10), -- GET, POST, PUT, DELETE
    status_code INTEGER,
    response_time INTEGER, -- ms
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### encryption_keys
暗号化鍵管理。
```sql
CREATE TABLE encryption_keys (
    key_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_version INTEGER,
    algorithm VARCHAR(20), -- AES-256-GCM
    encrypted_key_material TEXT, -- HSM等でラップされた鍵
    status VARCHAR(20), -- ACTIVE, ROTATED, REVOKED
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.7 バッチ管理 (Batch)

#### batch_jobs
```sql
CREATE TABLE batch_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name VARCHAR(100),
    status VARCHAR(20), -- RUNNING, COMPLETED, FAILED
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### interest_calc_log
利息計算ログ。
```sql
CREATE TABLE interest_calc_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(account_id),
    calculation_date DATE,
    interest_amount DECIMAL(19,4),
    balance_used DECIMAL(19,4),
    rate_used DECIMAL(5,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```
