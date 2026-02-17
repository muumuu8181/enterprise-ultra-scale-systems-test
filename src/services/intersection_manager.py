from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.models.intersection_models import IntersectionReservation

class IntersectionManager:
    """
    交差点予約管理サービス
    """

    async def reserve_slot(self, db: AsyncSession, intersection_id: int, vehicle_id: str,
                           arrival_time: datetime, duration_seconds: float = 2.0,
                           speed: float = 10.0, heading: float = 0.0, priority: bool = False) -> Optional[IntersectionReservation]:
        """
        スロットを予約する。
        競合がある場合はNoneを返す。
        """
        # 開始・終了時刻の計算
        slot_start = arrival_time
        slot_end = datetime.fromtimestamp(arrival_time.timestamp() + duration_seconds, tz=arrival_time.tzinfo)

        # 競合チェック
        if await self.check_conflicts(db, intersection_id, slot_start, slot_end):
            # 優先車両かつ競合相手が非優先ならキャンセルするなどのロジックがあり得るが、
            # ここではシンプルに予約失敗とする。
            return None

        reservation = IntersectionReservation(
            intersection_id=intersection_id,
            vehicle_id=vehicle_id,
            slot_start=slot_start,
            slot_end=slot_end,
            speed=speed,
            heading=heading,
            priority=priority
        )
        db.add(reservation)
        await db.commit()
        await db.refresh(reservation)
        return reservation

    async def check_conflicts(self, db: AsyncSession, intersection_id: int, start: datetime, end: datetime) -> bool:
        """
        予約の競合をチェックする。
        Trueなら競合あり。
        """
        # 時間が重なる予約があるか検索
        # (StartA < EndB) and (EndA > StartB)
        stmt = select(IntersectionReservation).where(
            IntersectionReservation.intersection_id == intersection_id,
            and_(
                IntersectionReservation.slot_start < end,
                IntersectionReservation.slot_end > start
            )
        )
        result = await db.execute(stmt)
        existing = result.scalars().first()
        return existing is not None

    async def implement_fcfs(self, db: AsyncSession, intersection_id: int) -> List[IntersectionReservation]:
        """
        FCFS (First-Come-First-Served) で予約リストを取得。
        """
        stmt = select(IntersectionReservation).where(
            IntersectionReservation.intersection_id == intersection_id
        ).order_by(IntersectionReservation.slot_start)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def implement_priority(self, db: AsyncSession, intersection_id: int) -> List[IntersectionReservation]:
        """
        緊急車両優先で予約リストを取得。
        priority=Trueの車両をリストの先頭に配置する。
        """
        stmt = select(IntersectionReservation).where(
            IntersectionReservation.intersection_id == intersection_id
        ).order_by(IntersectionReservation.priority.desc(), IntersectionReservation.slot_start)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def optimize_throughput(self, db: AsyncSession, intersection_id: int):
        """
        スループット最適化 (プレースホルダー)。
        """
        pass
