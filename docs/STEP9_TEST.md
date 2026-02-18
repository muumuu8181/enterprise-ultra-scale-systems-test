# Step 9: テスト仕様 (STEP9_TEST.md)

## 1. 概要
本ドキュメントは、ソフトウェアの品質を保証するためのテスト戦略とカバレッジ基準を定義する。
ミッションクリティカルなシステムであるため、特に単体テストと結合テストの網羅性を重視する。

- **目標テストコード行数**: 15,000行以上
- **目標カバレッジ**: 80% 以上（Coreモジュールは90%以上推奨）

## 2. 単体テスト (Unit Testing)

各モジュールのクラス・関数単位で動作を検証する。`pytest` を使用する。

### 2.1 顧客・口座モジュール (`tests/unit/`)
- **test_customer_service.py**
    - `register()`: 正常系、バリデーションエラー、重複エラー
    - `verify_kyc()`: ステータス遷移確認
- **test_account_service.py**
    - `open_account()`: 正常系、顧客状態エラー
    - `get_balance()`: 正しい残高取得
- **test_interest_calculator.py**
    - 利息計算の精度確認（小数点以下処理）
    - 境界値テスト（うるう年、月末、ゼロ金利）

### 2.2 取引モジュール
- **test_deposit_service.py**
    - 入金処理の原子性確認（モック使用）
    - 上限チェック
- **test_transfer_service.py**
    - `transfer_internal()` のモックテスト
    - デッドロック回避ロジック（ロック順序）の検証
- **test_limit_manager.py**
    - 日次・月次限度額の判定ロジック

### 2.3 トランザクション・基盤モジュール
- **test_two_phase_commit.py**
    - Prepare/Commit/Abort/Recover の各シーケンス
- **test_saga.py**
    - 補償トランザクション（Rollback）が正しく連鎖するか
- **test_encryption.py**
    - 暗号化・復号化の整合性
    - PIIデータの特定フィールドのみ暗号化されているか
- **test_audit_logger.py**
    - ログフォーマット確認
    - ハッシュチェーン生成ロジック

### 2.4 為替・融資モジュール
- **test_swift_parser.py**
    - MT103/MT202 メッセージのパース結果検証
- **test_repayment_scheduler.py**
    - 元利均等・元金均等計算結果がExcel計算等と一致するか
- **test_aml_detector.py**
    - 全検知パターンの網羅

## 3. 結合テスト (Integration Testing)

実際のDB（テスト用コンテナ）やメッセージキューを使用して、複数モジュールの連携を検証する。

### 3.1 業務シナリオテスト (`tests/integration/`)
- **test_deposit_flow.py**
    1. 口座開設
    2. 現金入金
    3. 残高確認
    4. 取引明細確認
    5. 監査ログ確認
- **test_transfer_flow.py**
    1. 口座A、口座B開設
    2. Aに入金
    3. AからBへ振込
    4. 両口座の残高整合性確認
    5. 限度額更新確認
- **test_loan_flow.py**
    1. 融資申込
    2. 審査承認
    3. 実行（入金）
    4. 返済（口座引落）
    5. 完済ステータス確認

### 3.2 並行性テスト (`tests/integration/test_concurrent.py`)
- **デッドロック耐性テスト**
    - 口座Aと口座Bの間で、A→B, B→A の振込を100スレッドで同時に実行する。
    - デッドロックエラーが発生せず、最終的な合計残高が一致することを確認する。
- **排他制御テスト**
    - 同一口座に対して、100回の同時入出金を行う。
    - 最終残高が論理的に正しい値（初期値 + 入金総額 - 出金総額）になっているか検証する。

## 4. テストデータ管理
- `db/seeds/` に定義された初期マスタ（口座種別、通貨、金利等）を使用する。
- テスト実行ごとにDBをクリーンアップ（またはロールバック）し、独立性を保つ。
