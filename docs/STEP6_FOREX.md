# Step 6: 為替・決済モジュール仕様 (STEP6_FOREX.md)

## 1. 概要
本ドキュメントは、外国為替（Forex）取引および決済（Settlement）処理の仕様を定義する。
SWIFT電文のパース、全銀フォーマット変換、RTGS（即時グロス決済）のロジックを含む。

## 2. 為替モジュール (`src/core/forex/`)

### 2.1 SWIFT 電文処理 (`swift_parser.py`)

国際送金の標準フォーマットである SWIFT MT メッセージを処理する。

#### Class: SwiftMessageParser

- `parse_mt103(raw: str) -> Mt103Message`
  - 顧客送金メッセージ (MT103) をパースし、構造化データに変換する。
  - 必須フィールド (Field 20, 32A, 50K, 59 等) の存在チェックを行う。
- `parse_mt202(raw: str) -> Mt202Message`
  - 銀行間送金メッセージ (MT202) をパースする。
- `generate_mt103(transfer: ForexTransfer) -> str`
  - 内部送金データから SWIFT MT103 電文を生成する。
- `validate_swift_bic(bic: str) -> bool`
  - BIC (Bank Identifier Code) のフォーマット (8桁 or 11桁) とチェックデジットを検証する。

### 2.2 為替レートサービス (`exchange_rate_service.py`)

#### Class: ExchangeRateService

- `get_current_rate(from_ccy, to_ccy) -> Decimal`
  - 指定通貨ペアの現在（最新）レートを取得する。
- `convert(amount, from_ccy, to_ccy) -> Decimal`
  - 金額を指定レートで換算する。スプレッド（手数料）を考慮する設定も可能。
- `update_rates(rates: List[RateUpdate]) -> None`
  - 外部プロバイダ（Reuters/Bloomberg API等）から取得したレートを一括更新する。
- `get_rate_history(pair, from_date, to_date) -> List[ExchangeRate]`
  - 過去のレート推移を取得する。

### 2.3 全銀システムアダプタ (`zengin_adapter.py`)

国内銀行間送金（内国為替）のフォーマット変換を行う。

#### Class: ZenginAdapter

- `encode_transfer(transfer: DomesticTransfer) -> str`
  - 振込依頼データを全銀固定長フォーマット（テキスト）に変換する。
  - 文字コードは JIS/EBCDIC 等の要件に従う（本システム内では UTF-8 で扱い、出力直前に変換）。
- `decode_transfer(raw: str) -> DomesticTransfer`
  - 受信した全銀データをパースする。
- `validate_bank_code(code: str) -> bool`
  - 統一金融機関コード（4桁）の妥当性を検証する。
- `validate_branch_code(code: str) -> bool`
  - 支店コード（3桁）の妥当性を検証する。

## 3. 決済モジュール (`src/core/settlement/`)

### 3.1 RTGS 決済サービス (`rtgs_service.py`)

Real-Time Gross Settlement（即時グロス決済）を処理する。

#### Class: RtgsService

- `submit_payment(payment: PaymentOrder) -> RtgsResult`
  - 決済指図を受け付け、日銀ネット等の外部システムへ送信する。
  - 資金不足時のキューイング機能を持つ。
- `confirm_settlement(settlement_id: UUID) -> Settlement`
  - 外部システムからの決済完了通知（引落通知）を受信し、内部ステータスを完了にする。
- `get_pending_settlements() -> List[Settlement]`
  - 未決済（キューイング中）の指図一覧を取得する。

### 3.2 ネット決済サービス (`net_settlement.py`)

時点ネット決済（Deferred Net Settlement）を行う。小口決済システム（全銀システム）等の差額計算。

#### Class: NetSettlementService

- `calculate_net_positions(participants: List[str], date: date) -> List[NetPosition]`
  - 参加金融機関ごとの受取額・支払額を集計し、ネット（差引）ポジションを算出する。
- `run_settlement_batch(date: date) -> BatchResult`
  - 決済日（通常は当日または翌営業日）にネット決済を実行するバッチ処理。
  - 各参加行の当座預金口座での資金移動を行う。
- `process_deferred_payments() -> int`
  - 繰延決済データを処理する。
