# Step 1: プロジェクト構造・用語集

## 1. プロジェクト構造詳細

### ディレクトリ構成
```
game-ops/
├── docs/               # プロジェクト仕様書
├── src/
│   ├── core/           # コアビジネスロジック (Service/Repository層)
│   │   ├── player/     # プレイヤー管理、認証、スタミナ
│   │   ├── gacha/      # ガチャエンジン、確率計算、天井ロジック
│   │   ├── event/      # ライブイベント、スコアボード、報酬配布
│   │   ├── inventory/  # アイテム管理、倉庫、強化
│   │   ├── billing/    # 課金決済、レシート検証、冪等性制御
│   │   ├── ranking/    # Redisベースの高速ランキングサービス (Go統合)
│   │   └── quest/      # クエスト進行、実績解除
│   ├── infrastructure/ # インフラ・技術基盤層
│   │   ├── db/         # SQLAlchemy DBセッション管理
│   │   ├── cache/      # Redisクライアント・コネクションプール
│   │   ├── messaging/  # Kafkaプロデューサー/コンシューマー
│   │   └── security/   # OAuth2.0、JWT署名、暗号化
│   └── api/            # APIエンドポイント (Controller層)
├── db/
│   ├── schema/         # DDL SQLファイル定義
│   └── migrations/     # AlembicによるDBマイグレーション
└── tests/
    ├── unit/           # Pytestによる単体テスト
    ├── integration/    # シナリオベースの結合テスト
    └── performance/    # Locustによる負荷テスト
```

## 2. 用語集 (Glossary)

### ユーザー・マーケティング関連
- **DAU (Daily Active Users):** 日次アクティブユーザー数。サービスの健全性指標。
- **MAU (Monthly Active Users):** 月次アクティブユーザー数。
- **ARPU (Average Revenue Per User):** ユーザー一人当たりの平均売上。
- **Retention Rate (RR):** 継続率 (翌日RR、7日RR、30日RR)。

### ガチャ関連
- **SR/SSR:** レアリティランク。Special Rare / Super Special Rare。
- **天井 (Pity System):** 一定回数ガチャを引いてもSSRが出ない場合に、強制的に排出または交換可能にする救済措置。
  - **ハード天井:** 完全に指定アイテムが手に入る確定措置。
  - **ソフト天井:** SSR確率が徐々に上昇する、またはSR以上確定などの緩和措置。
- **ピックアップ (Pickup):** 特定のキャラクターやアイテムの排出率が通常より高く設定される期間・施策。
- **Boxガチャ:** 箱の中身が決まっており、引き切るとリセット可能な形式。

### ゲームシステム関連
- **スタミナ (Stamina):** クエスト実行などに必要なリソース。時間経過やアイテムで回復する。
- **AP/SP (Action Points / Stamina Points):** 行動ポイント。GvGやレイドボスなど特定コンテンツ用のスタミナ。
- **GvG (Guild versus Guild):** ギルド対抗戦。
- **PvP (Player versus Player):** プレイヤー対戦。
- **レシート検証 (Receipt Verification):** App Store / Google Play ストアの購入レシートが正当なものか、各プラットフォームのAPIに問い合わせて確認する処理。不正課金（偽造レシート）を防ぐために必須。
- **冪等性 (Idempotency):** 同じ操作を何度行っても結果が変わらない性質。通信エラー時のリトライ処理などで二重課金や二重付与を防ぐために重要。
