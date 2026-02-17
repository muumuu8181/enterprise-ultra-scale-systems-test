# Step 7: 融資モジュール仕様 (STEP7_LOAN.md)

## 1. 概要
本ドキュメントは、融資（Lending）業務のライフサイクル（申込、審査、実行、返済、延滞管理）を管理するモジュールの仕様を定義する。

## 2. 融資管理モジュール (`src/core/loan/`)

### 2.1 融資サービス (`service.py`)

#### Class: LoanService

- `apply(customer_id, amount, loan_type, purpose) -> LoanApplication`
  - 融資申込を受け付ける。
  - 初期審査（信用スコアチェック）を行い、審査ワークフローを開始する。
- `approve(application_id, approver_id) -> Loan`
  - 審査承認を行い、融資契約（Loan）を作成する。
  - ステータスを `APPROVED` に更新する。
- `reject(application_id, reason) -> None`
  - 審査否決を行い、理由を記録する。
- `disburse(loan_id) -> Transaction`
  - 融資実行（貸出）。
  - 顧客の指定口座（Deposit Account）へ融資金を入金する。
  - トランザクション種別は `LOAN_DISBURSEMENT`。
- `get_balance(loan_id) -> LoanBalance`
  - 現在の元金残高、未収利息、遅延損害金を取得する。

### 2.2 返済スケジュール管理 (`repayment.py`)

#### Class: RepaymentScheduler

- `generate_equal_installment(loan: Loan) -> List[RepaymentSchedule]`
  - **元利均等返済**方式で返済予定表を作成する。
  - 毎回の返済額（元金＋利息）が一定になるように計算する（PMT関数相当）。
- `generate_equal_principal(loan: Loan) -> List[RepaymentSchedule]`
  - **元金均等返済**方式で返済予定表を作成する。
  - 毎回の元金返済額を固定し、利息は残高に応じて減少する。
- `calculate_prepayment_penalty(loan_id, prepay_date, amount) -> Decimal`
  - 繰上返済時の違約金（手数料）を計算する。

#### Class: RepaymentService

- `process_repayment(loan_id, amount, payment_date) -> RepaymentRecord`
  - 返済処理を実行する。
  - 入金額を以下の優先順位で充当する:
    1. 手数料・遅延損害金
    2. 未収利息
    3. 元金
  - 返済予定表（Schedule）のステータスを `PAID` に更新する。
- `handle_overdue(loan_id) -> OverdueRecord`
  - 返済期日を過ぎたローンに対し、ステータスを `OVERDUE` に変更し、遅延損害金を発生させる。
- `send_overdue_notices() -> int`
  - 延滞中の顧客に対し、督促メールや通知を送信する（バッチ処理）。

### 2.3 担保管理 (`collateral.py`)

#### Class: CollateralService

- `register(loan_id, collateral_type, description, valuation) -> Collateral`
  - 担保（不動産、有価証券等）を登録する。
  - 評価額（Valuation）を記録する。
- `revalue(collateral_id, new_valuation, date) -> Collateral`
  - 定期的な担保評価替え（再評価）を行い、評価額を更新する。
- `release(collateral_id) -> None`
  - 完済時などに担保を解除（抹消）する。
- `get_coverage_ratio(loan_id) -> Decimal`
  - 担保保全率（担保評価額 / 融資残高）を計算する。
  - 保全率が一定を下回った場合（LTV割れ）、追加担保要求のアラートを出す。
