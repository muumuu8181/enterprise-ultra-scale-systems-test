from typing import List, Optional, Dict, Any, Type
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, Column, String, Integer, DateTime, JSON
from sqlalchemy.orm import declarative_base

# イベント基底クラス
class DomainEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    aggregate_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: str

    class Config:
        frozen = True

# 具体的なイベント定義
class AccountCreated(DomainEvent):
    event_type: str = "AccountCreated"
    owner_id: str
    initial_balance: float = 0.0

class MoneyDeposited(DomainEvent):
    event_type: str = "MoneyDeposited"
    amount: float
    currency: str = "JPY"

class MoneyWithdrawn(DomainEvent):
    event_type: str = "MoneyWithdrawn"
    amount: float
    currency: str = "JPY"

class TransferInitiated(DomainEvent):
    event_type: str = "TransferInitiated"
    to_account_id: str
    amount: float
    currency: str = "JPY"

class TransferCompleted(DomainEvent):
    event_type: str = "TransferCompleted"
    transaction_id: str

class TransferFailed(DomainEvent):
    event_type: str = "TransferFailed"
    reason: str

# SQLAlchemy モデル (DB永続化用)
Base = declarative_base()

class EventModel(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    aggregate_id = Column(String, index=True, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    version = Column(Integer, nullable=False)

class SnapshotModel(Base):
    __tablename__ = "snapshots"

    aggregate_id = Column(String, primary_key=True)
    payload = Column(JSON, nullable=False)
    last_event_version = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)

class EventStore:
    """
    イベントソーシングの中核となるイベントストア。
    イベントの追記、取得、リプレイ、スナップショット作成を担当する。
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def append_event(self, event: DomainEvent, version: Optional[int] = None) -> None:
        """
        イベントを追記する。

        Args:
            event (DomainEvent): 保存するドメインイベント
            version (Optional[int]): 期待するバージョン（楽観的ロック用）。Noneの場合は自動採番（非推奨だがバッチ等で使用）。
        """
        if version is None:
            # バージョンが指定されていない場合、現在の最大バージョンを取得してインクリメント
            # Note: 競合の可能性があるため本来はロックが必要
            stmt = select(EventModel.version).where(
                EventModel.aggregate_id == event.aggregate_id
            ).order_by(EventModel.version.desc()).limit(1)
            result = await self.session.execute(stmt)
            current_max = result.scalar_one_or_none()
            version = (current_max or 0) + 1

        # ここでは簡略化のため直接DBモデルに変換して保存
        db_event = EventModel(
            id=str(event.event_id),
            aggregate_id=event.aggregate_id,
            event_type=event.event_type,
            payload=event.model_dump(mode='json'),
            timestamp=event.timestamp,
            version=version
        )
        self.session.add(db_event)
        # Note: commitは呼び出し元で行うか、ここでflushするかは設計次第だが、
        # 通常はUnitOfWorkパターンなどでまとめてコミットする。
        await self.session.flush()

    async def get_events_by_aggregate(self, aggregate_id: str) -> List[DomainEvent]:
        """
        集約IDに関連する全てのイベントを取得する。

        Args:
            aggregate_id (str): 集約ID

        Returns:
            List[DomainEvent]: イベントのリスト
        """
        stmt = select(EventModel).where(EventModel.aggregate_id == aggregate_id).order_by(EventModel.version)
        result = await self.session.execute(stmt)
        events_data = result.scalars().all()

        # DBモデルからドメインイベントへの変換ロジックが必要
        # 簡易的なファクトリ実装
        domain_events = []
        for db_event in events_data:
            event_cls = self._get_event_class(db_event.event_type)
            if event_cls:
                domain_events.append(event_cls(**db_event.payload))

        return domain_events

    async def replay_events(self, aggregate_id: str, initial_state: Any, reducer: callable) -> Any:
        """
        イベントをリプレイして現在の状態を構築する。

        Args:
            aggregate_id (str): 集約ID
            initial_state (Any): 初期状態
            reducer (callable): 状態遷移関数 (current_state, event) -> new_state

        Returns:
            Any: 最新の状態
        """
        events = await self.get_events_by_aggregate(aggregate_id)
        current_state = initial_state
        for event in events:
            current_state = reducer(current_state, event)
        return current_state

    async def create_snapshot(self, aggregate_id: str, state: Any, version: int) -> None:
        """
        スナップショットを作成する。

        Args:
            aggregate_id (str): 集約ID
            state (Any): 保存する状態オブジェクト（Serializableであること）
            version (int): 最後に適用されたイベントのバージョン
        """
        # 既存のスナップショットがあれば更新、なければ作成 (Upsert)
        # 簡略化のためdelete insertまたはmergeを使う
        # ここではPydanticモデルなどを想定してdictにダンプ
        payload = state.model_dump() if hasattr(state, "model_dump") else state.__dict__

        stmt = select(SnapshotModel).where(SnapshotModel.aggregate_id == aggregate_id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.payload = payload
            existing.last_event_version = version
            existing.timestamp = datetime.now()
        else:
            snapshot = SnapshotModel(
                aggregate_id=aggregate_id,
                payload=payload,
                last_event_version=version,
                timestamp=datetime.now()
            )
            self.session.add(snapshot)

        await self.session.flush()

    def _get_event_class(self, event_type: str) -> Optional[Type[DomainEvent]]:
        """イベントタイプ文字列からクラスを解決するヘルパー"""
        mapping = {
            "AccountCreated": AccountCreated,
            "MoneyDeposited": MoneyDeposited,
            "MoneyWithdrawn": MoneyWithdrawn,
            "TransferInitiated": TransferInitiated,
            "TransferCompleted": TransferCompleted,
            "TransferFailed": TransferFailed
        }
        return mapping.get(event_type)
