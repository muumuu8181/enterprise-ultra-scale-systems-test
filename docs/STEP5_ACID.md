# Step 5: トランザクション制御仕様 (STEP5_ACID.md)

## 1. 概要
本ドキュメントは、金融システムに不可欠なデータの整合性（ACID特性）を保証するためのインフラストラクチャ層の仕様を定義する。
特にマイクロサービス環境下における分散トランザクション制御に重点を置く。

## 2. トランザクション制御モジュール (`src/infrastructure/transaction/`)

### 2.1 Unit of Work (`unit_of_work.py`)

#### Class: UnitOfWork
SQLAlchemyのセッション管理を隠蔽し、リポジトリパターンと組み合わせて使用する。

- `__enter__() -> Self`
  - DBセッションを開始する。
- `__exit__(exc_type, exc_val, exc_tb) -> None`
  - 例外が発生した場合は `rollback()`、正常終了時は `commit()` を実行する。
- `register_new(entity: BaseEntity) -> None`
  - 新規作成エンティティを追跡対象にする。
- `register_dirty(entity: BaseEntity) -> None`
  - 変更されたエンティティを追跡対象にする。
- `register_deleted(entity: BaseEntity) -> None`
  - 削除対象エンティティを登録する。
- `commit() -> None`
  - 変更をDBに反映する。
- `rollback() -> None`
  - 変更を破棄する。

### 2.2 2相コミット (2PC) (`two_phase_commit.py`)

分散データベースや複数リソース間での整合性を確保する（主に同期的な整合性が必要な場合）。

#### Class: TwoPhaseCommitManager

- `prepare(participants: List[Participant]) -> PrepareResult`
  - 全参加リソースに対して `PREPARE` 要求を送信する。
  - 全員が `YES` を返した場合のみ、次のフェーズへ進む。
  - 1つでも `NO` またはタイムアウトの場合、`abort()` を呼び出す。
- `commit(transaction_id: UUID) -> None`
  - 全参加リソースに `COMMIT` 要求を送信する。
- `abort(transaction_id: UUID) -> None`
  - 全参加リソースに `ROLLBACK` 要求を送信する。
- `recover(transaction_id: UUID) -> None`
  - 障害発生時、未完了のトランザクション状態を確認し、commit/abort を再試行する。

### 2.3 Saga パターン (`saga.py`)

長時間のビジネストランザクションや、結果整合性で許容される処理（他行振込、非同期通知等）に使用する。

#### Class: SagaOrchestrator

- `execute(steps: List[SagaStep]) -> SagaResult`
  - 定義されたステップを順次実行する。
  - 途中のステップで失敗した場合、成功済みのステップに対して逆順に `compensation`（補償トランザクション）を実行する。

#### Class: SagaStep
- `action: Callable`: 実行する処理（正取引）。
- `compensation: Callable`: 失敗時の取消処理（逆取引）。
- `name: str`: ステップ名（ログ用）。

### 2.4 デッドロック制御 (`deadlock_handler.py`)

#### Class: DeadlockHandler

- `execute_with_retry(func: Callable, max_retries=3, backoff=0.1) -> Any`
  - 関数を実行し、SQLAlchemyの `OperationalError` (Deadlock detected) を捕捉する。
  - 指数バックオフ（Exponential Backoff）を用いて待機時間を増やしながらリトライする。
  - 最大リトライ回数を超えた場合はエラーを送出する。
- `detect_lock_timeout(func: Callable, timeout_sec=5) -> Any`
  - ロック待機時間が閾値を超えた場合にタイムアウトさせる。

### 2.5 分散ロック (`distributed_lock.py`)

Redisを用いた分散ロック機構。バッチ処理の二重起動防止や、クリティカルセクションの保護に使用。

#### Class: RedisDistributedLock

- `acquire(key: str, ttl_sec=30) -> bool`
  - `SET key value NX EX ttl_sec` を実行し、ロックを取得する。
- `release(key: str) -> None`
  - Luaスクリプトを使用し、自分のロック（valueが一致する場合）のみ削除するアトミック操作を行う。
- `extend(key: str, ttl_sec: int) -> bool`
  - 処理が長引く場合、ロックの有効期限を延長する。

### 2.6 Outbox パターン (`outbox.py`)

DB更新とメッセージ送信（Kafka）の原子性を保証する。

#### Class: OutboxPattern

- `save_event(event: DomainEvent, tx_session) -> None`
  - ドメインイベントをシリアライズし、`outbox` テーブルに INSERT する。
  - 業務データの更新と同一のDBトランザクションで行う。
- `publish_pending_events() -> int`
  - バックグラウンドワーカーが定期実行。
  - `outbox` テーブルから未送信イベントを取得し、Kafkaへ送信する。
  - 送信成功後、レコードを削除または送信済みフラグを更新する。
- `mark_published(event_id: UUID) -> None`
  - 送信完了を記録する。
