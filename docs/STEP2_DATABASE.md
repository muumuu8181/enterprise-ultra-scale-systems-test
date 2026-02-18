# Complete Database Schema (DDL)

## 1. 顧客関連 (Customer Domain)

```sql
-- 顧客マスタ
CREATE TABLE customers (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cif_number VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    date_of_birth DATE NOT NULL,
    nationality VARCHAR(3),
    tax_id VARCHAR(20) UNIQUE,
    kyc_status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (kyc_status IN ('PENDING','VERIFIED','REJECTED','EXPIRED')),
    risk_level VARCHAR(10) NOT NULL DEFAULT 'LOW'
        CHECK (risk_level IN ('LOW','MEDIUM','HIGH','BLOCKED')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_customers_cif ON customers(cif_number);
CREATE INDEX idx_customers_tax_id ON customers(tax_id);
CREATE INDEX idx_customers_kyc_status ON customers(kyc_status) WHERE deleted_at IS NULL;

-- 連絡先情報
CREATE TABLE customer_contacts (
    contact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    email VARCHAR(255),
    phone VARCHAR(20),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(3),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_contacts_customer_id ON customer_contacts(customer_id);

-- 本人確認書類
CREATE TABLE customer_documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('PASSPORT', 'DRIVERS_LICENSE', 'MY_NUMBER')),
    document_number VARCHAR(100),
    expiry_date DATE,
    s3_key VARCHAR(512) NOT NULL,
    verification_status VARCHAR(20) DEFAULT 'PENDING',
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    verified_at TIMESTAMPTZ
);
CREATE INDEX idx_docs_customer_id ON customer_documents(customer_id);

-- 顧客リスク評価
CREATE TABLE customer_risk (
    risk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    risk_score INT,
    risk_factors JSONB,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    evaluator_id UUID
);
CREATE INDEX idx_risk_customer_id ON customer_risk(customer_id);
```

## 2. 口座関連 (Account Domain)

```sql
-- 口座マスタ
CREATE TABLE accounts (
    account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_number VARCHAR(20) UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    account_type VARCHAR(20) NOT NULL
        CHECK (account_type IN ('SAVINGS','CURRENT','TIME_DEPOSIT','ORDINARY')),
    balance DECIMAL(19,4) NOT NULL DEFAULT 0 CHECK (balance >= 0),
    available_balance DECIMAL(19,4) NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'JPY',
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE','FROZEN','CLOSED','DORMANT')),
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_accounts_customer_id ON accounts(customer_id);
CREATE INDEX idx_accounts_account_number ON accounts(account_number);
CREATE INDEX idx_accounts_status ON accounts(status) WHERE status = 'ACTIVE';

-- 口座種別マスタ
CREATE TABLE account_types (
    type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    currency VARCHAR(3) DEFAULT 'JPY',
    description TEXT
);

-- 金利マスタ
CREATE TABLE interest_rates (
    rate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_type_id UUID REFERENCES account_types(type_id),
    rate DECIMAL(5,4) NOT NULL, -- e.g. 0.0010 for 0.1%
    valid_from DATE NOT NULL,
    valid_to DATE
);
CREATE INDEX idx_rates_type_date ON interest_rates(account_type_id, valid_from);

-- 口座取引限度額
CREATE TABLE account_limits (
    limit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    daily_limit DECIMAL(19,4),
    transaction_limit DECIMAL(19,4),
    monthly_limit DECIMAL(19,4),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_limits_account_id ON account_limits(account_id);
```

## 3. 取引関連 (Transaction Domain)

```sql
-- 取引履歴（月次パーティション）
CREATE TABLE transactions (
    transaction_id UUID NOT NULL DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    transaction_type VARCHAR(30) NOT NULL
        CHECK (transaction_type IN ('DEPOSIT','WITHDRAWAL','TRANSFER_IN','TRANSFER_OUT','INTEREST','FEE','REVERSAL')),
    amount DECIMAL(19,4) NOT NULL CHECK (amount > 0),
    balance_after DECIMAL(19,4) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'JPY',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING','COMPLETED','FAILED','REVERSED')),
    reference_id UUID,
    description TEXT,
    channel VARCHAR(20) CHECK (channel IN ('ATM','COUNTER','ONLINE','INTERNAL','BATCH')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    PRIMARY KEY (transaction_id, created_at)
) PARTITION BY RANGE (created_at);

CREATE TABLE transactions_2024_01 PARTITION OF transactions
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE transactions_2024_02 PARTITION OF transactions
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE INDEX idx_transactions_account_id ON transactions(account_id, created_at DESC);
CREATE INDEX idx_transactions_status ON transactions(status) WHERE status = 'PENDING';

-- 取引詳細情報
CREATE TABLE transaction_details (
    detail_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL, -- Partitioning makes FK tricky, handled by app logic usually or carefully designed
    metadata JSONB, -- Additional details
    sender_name VARCHAR(200),
    receiver_name VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_tx_details_tx_id ON transaction_details(transaction_id);

-- 保留中取引
CREATE TABLE pending_transactions (
    pending_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    amount DECIMAL(19,4) NOT NULL,
    transaction_type VARCHAR(30),
    expiry_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'HELD',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_pending_account_expiry ON pending_transactions(account_id, expiry_at);
```

## 4. 為替・国際送金 (Forex & International)

```sql
-- 外国為替取引
CREATE TABLE forex_transactions (
    forex_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL,
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    from_amount DECIMAL(19,4) NOT NULL,
    to_amount DECIMAL(19,4) NOT NULL,
    rate DECIMAL(19,8) NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_forex_tx_id ON forex_transactions(transaction_id);

-- 為替レート履歴
CREATE TABLE exchange_rates (
    rate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    currency_pair VARCHAR(7) NOT NULL, -- e.g. USD/JPY
    rate DECIMAL(19,8) NOT NULL,
    source VARCHAR(50),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_rates_pair_time ON exchange_rates(currency_pair, timestamp DESC);

-- SWIFT電文ログ
CREATE TABLE swift_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID,
    mt_type VARCHAR(10) NOT NULL, -- e.g. MT103
    sender_bic VARCHAR(11) NOT NULL,
    receiver_bic VARCHAR(11) NOT NULL,
    raw_message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'SENT',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_swift_tx_id ON swift_messages(transaction_id);

-- 全銀データ
CREATE TABLE zengin_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID,
    bank_code VARCHAR(4),
    branch_code VARCHAR(3),
    account_type VARCHAR(1),
    account_number VARCHAR(7),
    account_name VARCHAR(200),
    amount DECIMAL(19,4),
    status VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_zengin_tx_id ON zengin_records(transaction_id);
```

## 5. 融資 (Loans Domain)

```sql
-- 融資商品マスタ
CREATE TABLE loan_types (
    type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    interest_rate_model VARCHAR(50), -- FIXED, VARIABLE
    base_rate DECIMAL(5,4),
    min_term_months INT,
    max_term_months INT
);

-- 融資申込
CREATE TABLE loan_applications (
    application_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    loan_type_id UUID NOT NULL REFERENCES loan_types(type_id),
    amount_requested DECIMAL(19,4) NOT NULL,
    term_months INT,
    purpose TEXT,
    status VARCHAR(20) DEFAULT 'APPLIED',
    reviewed_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);
CREATE INDEX idx_apps_customer_status ON loan_applications(customer_id, status);

-- 融資契約
CREATE TABLE loans (
    loan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES loan_applications(application_id),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    principal_amount DECIMAL(19,4) NOT NULL,
    outstanding_balance DECIMAL(19,4) NOT NULL,
    interest_rate DECIMAL(5,4) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','PAID_OFF','DEFAULTED')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_loans_customer_id ON loans(customer_id);

-- 返済予定表
CREATE TABLE repayment_schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID NOT NULL REFERENCES loans(loan_id),
    due_date DATE NOT NULL,
    principal_amount DECIMAL(19,4) NOT NULL,
    interest_amount DECIMAL(19,4) NOT NULL,
    total_amount DECIMAL(19,4) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING','PAID','OVERDUE')),
    paid_at TIMESTAMPTZ
);
CREATE INDEX idx_schedules_loan_date ON repayment_schedules(loan_id, due_date);

-- 返済履歴
CREATE TABLE repayment_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID NOT NULL REFERENCES loans(loan_id),
    payment_amount DECIMAL(19,4) NOT NULL,
    principal_portion DECIMAL(19,4),
    interest_portion DECIMAL(19,4),
    penalty_amount DECIMAL(19,4) DEFAULT 0,
    paid_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_history_loan_date ON repayment_history(loan_id, paid_at);

-- 担保情報
CREATE TABLE collaterals (
    collateral_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID REFERENCES loans(loan_id),
    type VARCHAR(50) NOT NULL, -- REAL_ESTATE, SECURITIES
    description TEXT,
    valuation_amount DECIMAL(19,4) NOT NULL,
    valuation_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE'
);
CREATE INDEX idx_collaterals_loan_id ON collaterals(loan_id);
```

## 6. 決済・清算 (Settlement Domain)

```sql
-- 決済処理
CREATE TABLE settlements (
    settlement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL,
    settlement_method VARCHAR(20),
    clearing_house VARCHAR(50), -- ZENGIN, BOJ-NET
    status VARCHAR(20) DEFAULT 'PENDING',
    settled_at TIMESTAMPTZ
);
CREATE INDEX idx_settlements_tx_id ON settlements(transaction_id);

-- RTGS取引
CREATE TABLE rtgs_transactions (
    rtgs_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID,
    message_type VARCHAR(20),
    instruction_id VARCHAR(50) UNIQUE,
    status VARCHAR(20)
);

-- 決済ネットポジション
CREATE TABLE net_positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_code VARCHAR(4) NOT NULL,
    clearing_date DATE NOT NULL,
    net_amount DECIMAL(19,4) NOT NULL, -- Positive: Receive, Negative: Pay
    currency VARCHAR(3) DEFAULT 'JPY',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_positions_bank_date ON net_positions(bank_code, clearing_date);

-- 支払指図
CREATE TABLE payment_orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    beneficiary_account VARCHAR(50),
    beneficiary_bank VARCHAR(50),
    amount DECIMAL(19,4) NOT NULL,
    execution_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'SCHEDULED'
);
CREATE INDEX idx_orders_account_date ON payment_orders(account_id, execution_date);
```

## 7. 管理・セキュリティ (Admin & Security)

```sql
-- 権限ロール
CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(50) UNIQUE NOT NULL, -- TELLER, MANAGER, AUDITOR, ADMIN
    permissions JSONB NOT NULL, -- List of allowed actions
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 行内ユーザー
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role_id UUID REFERENCES roles(role_id),
    email VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);
CREATE INDEX idx_users_username ON users(username);

-- 監査ログ
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,
    target_resource VARCHAR(100),
    target_id UUID,
    details JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    prev_hash VARCHAR(64) -- Hash chain for tamper evidence
);
CREATE INDEX idx_audit_user_time ON audit_logs(user_id, timestamp);

-- アクセスログ
CREATE TABLE access_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    ip_address VARCHAR(45),
    endpoint VARCHAR(200),
    method VARCHAR(10),
    status_code INT,
    latency_ms INT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 暗号鍵管理
CREATE TABLE encryption_keys (
    key_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_version INT NOT NULL,
    algorithm VARCHAR(20) DEFAULT 'AES-256-GCM',
    key_material_encrypted TEXT NOT NULL, -- Encrypted by Master Key (HSM)
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    rotated_at TIMESTAMPTZ
);
CREATE INDEX idx_keys_version ON encryption_keys(key_version);

-- バッチジョブ管理
CREATE TABLE batch_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name VARCHAR(100) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'RUNNING',
    records_processed INT DEFAULT 0,
    error_message TEXT
);
CREATE INDEX idx_jobs_status_time ON batch_jobs(status, start_time);

-- 利息計算ログ
CREATE TABLE interest_calc_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    calculation_date DATE NOT NULL,
    balance DECIMAL(19,4),
    interest_rate DECIMAL(5,4),
    interest_amount DECIMAL(19,4),
    tax_amount DECIMAL(19,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_interest_account_period ON interest_calc_log(account_id, calculation_date);
```
