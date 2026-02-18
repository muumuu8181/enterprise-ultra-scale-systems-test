# Database Schema Overview

## テーブル一覧

| テーブル名 | 目的 | 主要カラム | インデックス |
|---|---|---|---|
| customers | 顧客マスタ | customer_id, name, tax_id, kyc_status | idx_customers_tax_id, idx_customers_status |
| customer_contacts | 連絡先情報 | contact_id, customer_id, email, phone | idx_contacts_customer_id |
| customer_documents | 本人確認書類 | document_id, customer_id, doc_type, s3_key | idx_docs_customer_id |
| customer_risk | 顧客リスク評価 | risk_id, customer_id, risk_level, score | idx_risk_customer_id |
| accounts | 口座マスタ | account_id, account_number, balance | idx_accounts_account_number, idx_accounts_customer |
| account_types | 口座種別マスタ | type_id, code, name, currency | idx_account_types_code |
| interest_rates | 金利マスタ | rate_id, account_type_id, rate, valid_from | idx_rates_type_date |
| account_limits | 口座取引限度額 | limit_id, account_id, daily_limit | idx_limits_account_id |
| transactions | 取引履歴（パーティション） | transaction_id, account_id, amount, status | idx_transactions_account_date |
| transaction_details | 取引詳細情報 | detail_id, transaction_id, metadata | idx_tx_details_tx_id |
| pending_transactions | 保留中取引 | pending_id, account_id, amount, expiry | idx_pending_account_expiry |
| forex_transactions | 外国為替取引 | forex_id, transaction_id, from_curr, to_curr | idx_forex_tx_id |
| exchange_rates | 為替レート履歴 | rate_id, currency_pair, rate, timestamp | idx_rates_pair_time |
| swift_messages | SWIFT電文ログ | message_id, transaction_id, mt_type, raw_data | idx_swift_tx_id |
| zengin_records | 全銀データ | record_id, transaction_id, bank_code, status | idx_zengin_tx_id |
| loans | 融資契約 | loan_id, customer_id, principal, status | idx_loans_customer_id |
| loan_types | 融資商品マスタ | type_id, name, base_rate, max_term | idx_loan_types_name |
| repayment_schedules | 返済予定表 | schedule_id, loan_id, due_date, amount | idx_schedules_loan_date |
| repayment_history | 返済履歴 | history_id, loan_id, paid_amount, paid_date | idx_history_loan_date |
| collaterals | 担保情報 | collateral_id, loan_id, type, valuation | idx_collaterals_loan_id |
| loan_applications | 融資申込 | application_id, customer_id, amount, status | idx_apps_customer_status |
| settlements | 決済処理 | settlement_id, transaction_id, method, status | idx_settlements_tx_id |
| rtgs_transactions | RTGS取引 | rtgs_id, transaction_id, message_type | idx_rtgs_tx_id |
| net_positions | 決済ネットポジション | position_id, bank_code, amount, date | idx_positions_bank_date |
| payment_orders | 支払指図 | order_id, account_id, beneficiary, amount | idx_orders_account_date |
| users | 行内ユーザー | user_id, username, role_id, email | idx_users_username |
| roles | 権限ロール | role_id, name, permissions | idx_roles_name |
| audit_logs | 監査ログ | log_id, user_id, action, target_id, timestamp | idx_audit_user_time |
| access_logs | アクセスログ | log_id, user_id, ip_address, endpoint | idx_access_user_time |
| encryption_keys | 暗号鍵管理 | key_id, version, algorithm, created_at | idx_keys_version |
| batch_jobs | バッチジョブ管理 | job_id, job_name, status, start_time | idx_jobs_status_time |
| interest_calc_log | 利息計算ログ | log_id, account_id, interest_amount, period | idx_interest_account_period |
| branches | 支店マスタ | branch_id, code, name, address | idx_branches_code |
| atms | ATM端末マスタ | atm_id, branch_id, status, cash_balance | idx_atms_branch |
| cards | キャッシュカード | card_id, account_id, card_number, status | idx_cards_number |
| card_transactions | カード取引履歴 | tx_id, card_id, amount, merchant | idx_card_tx_card_date |
| currencies | 通貨マスタ | currency_code, name, symbol, decimals | idx_currencies_code |
| holidays | 休日カレンダー | date, country_code, description | idx_holidays_date |
| fees | 手数料マスタ | fee_id, transaction_type, amount, currency | idx_fees_type |
| fee_schedule | 手数料適用ルール | schedule_id, customer_rank, fee_id | idx_fee_schedule_rank |
| notifications | 通知履歴 | notification_id, customer_id, type, status | idx_notifications_cust_time |
| notification_templates | 通知テンプレート | template_id, type, subject, body | idx_templates_type |
| tax_rates | 税率マスタ | tax_id, type, rate, effective_date | idx_tax_type_date |
| compliance_checks | コンプライアンスチェック | check_id, transaction_id, rule_id, result | idx_compliance_tx_id |
| sanction_lists | 制裁リスト | list_id, name, nationality, date_of_birth | idx_sanction_name |
| api_keys | 外部連携APIキー | key_id, client_name, api_key_hash, scopes | idx_api_keys_client |
| webhooks | Webhook設定 | webhook_id, event_type, url, secret | idx_webhooks_event |
| system_settings | システム設定 | key, value, description, updated_at | idx_settings_key |
| error_logs | エラーログ | log_id, service_name, error_code, stack_trace | idx_errors_service_time |
| login_attempts | ログイン試行履歴 | attempt_id, username, ip_address, success | idx_login_user_time |
