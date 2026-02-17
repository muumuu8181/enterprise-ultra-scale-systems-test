# Step 9: セキュリティ・不正対策仕様

## 1. 概要
本システムは、不正アクセス、チート行為、DoS攻撃からシステムを保護し、公平性を維持するための多層防御機能を実装する。

## 2. 不正対策・チート検知 (`FraudDetector`)

### 2.1 異常スコア検知 (Score Anomaly Detection)
`src/core/antifraud/detector.py`

- **Z-Score分析:**
  - イベントスコアやランキングスコアの分布を統計的に監視。
  - `z-score > 3σ` (標準偏差の3倍) を超える異常値を自動フラグ付け。
  - フラグ付きユーザーはランキング一時除外または監視対象リスト入り。

- **リプレイ検証:**
  - 高スコア達成時の `battle_log` (行動履歴JSON) をサーバーサイドで簡易シミュレーションし、実現可能性を検証。

### 2.2 ガチャ確率・排出監視
`src/core/antifraud/gacha_audit.py`

- **排出率リアルタイムモニタリング:**
  - Prometheus + Grafana で SSR排出率を監視。
  - 設定値 (1.0%) から有意に乖離した場合 (例: 0.5%以下 または 1.5%以上)、即座にアラート発報。
  - PagerDuty連携による緊急対応フロー。

### 2.3 課金速度制限 (Billing Velocity Check)
`src/core/antifraud/billing_limit.py`

- **短時間大量課金検知:**
  - 同一IP/デバイスからの連続購入試行をRedisでカウント。
  - `1分間に5回以上` または `1時間に10万円以上` の場合、一時ロック。

## 3. APIセキュリティ

### 3.1 レート制限 (Rate Limiting)
`src/infrastructure/security/limiter.py`

- **Token Bucket Algorithm (Redis):**
  - エンドポイントごとにバースト許容値を設定。
  - 一般API: 100 req/min
  - 認証API: 10 req/min (総当たり攻撃対策)
  - ガチャAPI: 60 req/min (連打対策)

### 3.2 認証・暗号化
`src/infrastructure/security/crypto.py`

- **通信経路:** 全て HTTPS (TLS 1.2以上) 必須。
- **パスワード:** 保存しない (OAuthのみ)。
- **機密情報:** `Vault` または AWS KMS で管理し、環境変数に直接記載しない。
- **署名検証:** クライアントからの重要リクエストにはHMAC署名を付与し、改ざん防止。

## 4. アプリケーション保護
- **難読化:** iOS/Androidアプリコードの難読化 (Obfuscation)。
- **Root/Jailbreak検知:** 起動時に検知し、APIアクセスを拒否。
- **SSL Pinning:** 中間者攻撃 (MITM) 防止。
