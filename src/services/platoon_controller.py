from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from src.models.platooning_models import PlatoonGroup, PlatoonMember

class PlatoonController:
    """
    隊列走行コントローラー
    Platoon Controller Service
    """

    async def form_platoon(
        self,
        db: AsyncSession,
        leader_id: str,
        max_members: int,
        target_speed: float,
        spacing_distance: float = 10.0
    ) -> PlatoonGroup:
        """
        新しい隊列を作成する。
        Create a new platoon group.
        """
        group = PlatoonGroup(
            leader_id=leader_id,
            target_speed=target_speed,
            spacing_distance=spacing_distance,
            status="forming",
            member_count=1
        )
        db.add(group)
        await db.commit()
        await db.refresh(group)

        # リーダーをメンバーとして追加
        member = PlatoonMember(
            group_id=group.id,
            vehicle_id=leader_id,
            position_in_platoon=1
        )
        db.add(member)
        await db.commit()

        return group

    async def join_platoon(
        self,
        db: AsyncSession,
        group_id: int,
        vehicle_id: str,
        position: int
    ) -> Optional[PlatoonMember]:
        """
        隊列に参加する。
        Join an existing platoon.
        """
        result = await db.execute(select(PlatoonGroup).where(PlatoonGroup.id == group_id))
        group = result.scalar_one_or_none()
        if not group:
            return None # Or raise exception

        member = PlatoonMember(
            group_id=group_id,
            vehicle_id=vehicle_id,
            position_in_platoon=position
        )
        db.add(member)

        group.member_count += 1

        await db.commit()
        await db.refresh(member)
        return member

    async def leave_platoon(
        self,
        db: AsyncSession,
        group_id: int,
        vehicle_id: str
    ) -> bool:
        """
        隊列から離脱する。
        Leave a platoon.
        """
        result = await db.execute(select(PlatoonMember).where(
            PlatoonMember.group_id == group_id,
            PlatoonMember.vehicle_id == vehicle_id
        ))
        member = result.scalar_one_or_none()
        if member:
            await db.delete(member)

            # メンバー数を更新
            group_result = await db.execute(select(PlatoonGroup).where(PlatoonGroup.id == group_id))
            group = group_result.scalar_one_or_none()
            if group:
                group.member_count = max(0, group.member_count - 1)
                # リーダーが抜けた場合の処理などが必要かもしれないが、
                # ここでは簡易実装とする。

            await db.commit()
            return True
        return False

    async def dissolve_platoon(self, db: AsyncSession, group_id: int) -> bool:
        """
        隊列を解散する。
        Dissolve the platoon.
        """
        result = await db.execute(select(PlatoonGroup).where(PlatoonGroup.id == group_id))
        group = result.scalar_one_or_none()
        if group:
            group.status = "dissolved"
            group.member_count = 0

            # 全メンバー削除
            await db.execute(delete(PlatoonMember).where(PlatoonMember.group_id == group_id))

            await db.commit()
            return True
        return False

    async def maintain_spacing(self, db: AsyncSession, group_id: int) -> None:
        """
        車間距離維持制御（プレースホルダー）。
        Maintain spacing between vehicles.
        """
        # 実実装では車両への制御メッセージ送信などがここに入る
        pass

    async def handle_emergency_brake(self, db: AsyncSession, group_id: int) -> None:
        """
        緊急ブレーキ対応。
        Handle emergency braking.
        """
        result = await db.execute(select(PlatoonGroup).where(PlatoonGroup.id == group_id))
        group = result.scalar_one_or_none()
        if group:
            group.status = "emergency_braking"
            group.target_speed = 0.0
            # 全車両へ停止命令をブロードキャストする処理などがここに入る
            await db.commit()
