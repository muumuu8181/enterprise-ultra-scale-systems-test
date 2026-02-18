# Step 8: セキュリティ・監査モジュール仕様 (STEP8_SECURITY.md)

## 1. 概要
本ドキュメントは、銀行システムの要となるセキュリティ（認証・認可・暗号化）および監査ログ（Audit Logging）の仕様を定義する。
PCI DSS や Fisc 安全対策基準などのガイドラインに準拠することを目指す。

## 2. セキュリティインフラ (`src/infrastructure/security/`)

### 2.1 認証サービス (`auth_service.py`)

#### Class: AuthService

- `login(user_id, password) -> AuthResult`
  - ユーザーIDとパスワードを検証し、JWT (JSON Web Token) を発行する。
  - パスワードは `bcrypt` 等でハッシュ化して保存・検証する。
- `verify_totp(user_id, totp_code) -> bool`
  - 二要素認証 (MFA)。Google Authenticator 等の Time-based OTP を検証する。
  - 管理者権限や高額取引承認時には必須とする。
- `issue_token(user_id, scopes) -> JwtToken`
  - アクセストークン（有効期限短）とリフレッシュトークン（有効期限長）を発行する。
- `revoke_token(token) -> None`
  - ログアウト時やトークン流出疑義時に、トークンを無効化（ブラックリスト登録）する。
- `refresh_token(refresh_token) -> JwtToken`
  - 有効なリフレッシュトークンを用いて、新しいアクセストークンを発行する。

### 2.2 アクセス制御 (`rbac.py`)

Role-Based Access Control (RBAC) を実装する。

#### Class: RbacManager

- `check_permission(user_id, resource, action) -> bool`
  - 指定されたユーザーが、特定のリソース（例: 口座情報）に対して特定のアクション（例: 閲覧、更新）を行う権限があるか判定する。
- `get_user_roles(user_id) -> List[Role]`
  - ユーザーに割り当てられたロール一覧を取得する。
- `assign_role(user_id, role) -> None`
  - ユーザーにロールを付与する（Adminのみ実行可能）。
- **Role Types**:
  - `TELLER`: 窓口担当者（入出金操作、顧客検索）
  - `MANAGER`: 支店長（承認権限、限度額オーバーライド）
  - `AUDITOR`: 監査人（ログ閲覧のみ）
  - `ADMIN`: システム管理者（ユーザー管理、マスタ設定）
  - `READONLY`: 参照専用

### 2.3 暗号化サービス (`encryption.py`)

#### Class: EncryptionService

- `encrypt(plaintext: str) -> str`
  - データベースに保存する機密情報（PII: 個人特定情報）を暗号化する。
  - アルゴリズム: AES-256-GCM。
  - 鍵管理: KMS または HSM からデータキーを取得して使用する（Envelope Encryption）。
- `decrypt(ciphertext: str) -> str`
  - 暗号文を復号する。
- `encrypt_pii(data: dict) -> dict`
  - 辞書オブジェクト内の特定フィールド（`tax_id`, `phone`, `address` 等）のみを再帰的に暗号化する。
- `hash_password(password: str) -> str`
  - パスワードをソルト付きハッシュ化する（bcrypt/Argon2）。
- `verify_password(password, hash) -> bool`
  - 入力パスワードと保存ハッシュを照合する。

## 3. 監査モジュール (`src/infrastructure/audit/`)

### 3.1 監査ロガー (`audit_logger.py`)

全ての操作を改ざん不可能な形式で記録する。

#### Class: AuditLogger

- `log(user_id, action, target_table, target_id, before, after, ip) -> None`
  - **必須項目**:
    - `timestamp`: 操作日時（UTC）
    - `actor`: 操作者ID
    - `action`: 操作内容（CREATE/UPDATE/DELETE/VIEW）
    - `resource`: 対象リソース
    - `changes`: 変更前後の差分（JSON）
    - `context`: IPアドレス、User-Agent、RequestID
  - ログは非同期でDBへ書き込み、パフォーマンスへの影響を最小限にする。
- `log_access(user_id, endpoint, method, status_code, response_time) -> None`
  - APIアクセスログを記録する。
- `query(filters: AuditFilter, page, size) -> Page[AuditLog]`
  - 監査担当者がログを検索・閲覧するためのインターフェース。

### 3.2 改ざん検知 (`tamper_detector.py`)

#### Class: TamperDetector

- `compute_hash(log_entry: AuditLog) -> str`
  - ログエントリの内容と直前のログのハッシュ値を組み合わせてハッシュ計算を行う（ブロックチェーン的な構造）。
  - `current_hash = SHA256(prev_hash + log_data)`
- `verify_chain(from_date, to_date) -> VerificationResult`
  - 指定期間のログチェーンを再計算し、DB保存値と一致するか検証する。
  - 不整合があれば、改ざんが発生した箇所（Log ID）を特定する。
- `detect_gap(log_ids: List[int]) -> List[int]`
  - 連番（Sequence Number）の欠番を検出し、ログの削除を検知する。

### 3.3 AML検知 (`aml_detector.py`)

マネーロンダリング対策（Anti-Money Laundering）。

#### Class: AmlDetector

- `check_transaction(tx: Transaction) -> AmlResult`
  - 取引発生時にリアルタイム（または準リアルタイム）でチェックを行う。
  - **検知ルール例**:
    - 1回 1000万円以上の現金取引 → `MANDATORY_REPORT`
    - 短時間（例: 1時間以内）に同一口座への複数回の振込 → `SUSPICIOUS_ACTIVITY`
    - 送金先が制裁対象国・個人リスト（Sanction List）に含まれる → `BLOCKED`
