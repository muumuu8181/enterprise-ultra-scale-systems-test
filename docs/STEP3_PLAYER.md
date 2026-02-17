# Step 3: プレイヤー管理・認証仕様

## 1. 概要
プレイヤー管理モジュールは、ユーザーの新規登録、認証、基本ステータス管理、スタミナ回復などのコア機能を提供する。
認証にはOAuth 2.0 (Apple, Google, Twitter) を使用し、セッション管理にはJWTを用いる。

## 2. クラス・コンポーネント設計

### 2.1 データモデル (SQLAlchemy ORM)
`src/core/player/models.py`

- **Player:** ユーザー基本情報
- **PlayerAuth:** 外部ID連携情報
- **PlayerStats:** 頻繁に更新される数値データ (Exp, Stamina, Gems)

### 2.2 サービス層 (`PlayerService`)
`src/core/player/service.py`

| メソッド名 | 引数 | 戻り値 | 説明 |
| :--- | :--- | :--- | :--- |
| `register` | `provider`, `provider_uid`, `username` | `Player` | 新規ユーザー作成 |
| `login` | `provider`, `token` | `AuthResult` | 外部トークン検証とJWT発行 |
| `get_player` | `player_id` | `PlayerResponse` | プロフィール取得 |
| `update_stats` | `player_id`, `updates` | `PlayerStats` | 経験値加算等の更新 |
| `recover_stamina` | `player_id` | `None` | 時間経過によるスタミナ回復計算 |
| `consume_stamina` | `player_id`, `amount` | `bool` | スタミナ消費 (不足時False) |

### 2.3 認証・セキュリティ (`AuthManager`)
`src/infrastructure/security/auth.py`

- **JWT仕様:**
  - アルゴリズム: RS256 (秘密鍵/公開鍵)
  - Access Token有効期限: 60分
  - Refresh Token有効期限: 30日
  - ペイロード: `sub` (player_id), `role`, `iat`, `exp`

- **OAuth検証:**
  - `verify_apple_token(identity_token)`: Apple Public Keysを取得して署名検証
  - `verify_google_token(id_token)`: Google Auth Libraryを使用

## 3. APIエンドポイント定義 (`FastAPI`)

| メソッド | パス | 説明 | 認証 |
| :--- | :--- | :--- | :--- |
| POST | `/v1/auth/login` | ソーシャルログイン | 不要 |
| POST | `/v1/auth/refresh` | トークン更新 | Refresh Token |
| GET | `/v1/player/me` | 自身の情報取得 | 必要 |
| PATCH | `/v1/player/me/profile` | プロフィール更新 | 必要 |
| POST | `/v1/player/stamina/recover` | アイテムによるスタミナ回復 | 必要 |

## 4. スタミナ回復ロジック
スタミナは「時間経過」と「アイテム/石消費」の2パターンで回復する。

- **時間回復:**
  - 5分に1ポイント回復 (設定可能)
  - `max_stamina` を超えては回復しない
  - 計算式: `回復量 = (現在時刻 - 最終更新時刻) / 回復間隔`
  - DB更新は「APIアクセス時」または「バッチ処理時」に行う (Lazy Evaluation)

- **オーバーフロー:**
  - アイテムや石による回復は上限を超えて回復可能 (例: 100/100 -> 150/100)
