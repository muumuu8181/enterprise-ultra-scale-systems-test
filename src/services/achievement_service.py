from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from src.models.achievement_models import Achievement, UserAchievement

class AchievementService:
    """実績システムのロジックを担当するサービスクラス"""

    async def get_all_achievements(self, db: AsyncSession):
        """全ての実績定義を取得する"""
        result = await db.execute(select(Achievement))
        return result.scalars().all()

    async def get_user_achievements(self, db: AsyncSession, user_id: int):
        """
        ユーザーの獲得済み実績を取得する
        Achievement情報もEager Loadする
        """
        stmt = select(UserAchievement).where(
            UserAchievement.user_id == user_id
        ).options(selectinload(UserAchievement.achievement))

        result = await db.execute(stmt)
        return result.scalars().all()

    async def unlock_achievement(self, db: AsyncSession, user_id: int, achievement_id: int):
        """
        指定された実績を強制的に解放する（デバッグ用・手動用）
        """
        stmt = select(UserAchievement).where(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id
        ).options(selectinload(UserAchievement.achievement))
        result = await db.execute(stmt)
        ua = result.scalar_one_or_none()

        if not ua:
            ua = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id,
                progress={"current": 0} # デフォルト
            )
            db.add(ua)
            await db.flush()
            # Relationshipをロードするためにrefresh
            await db.refresh(ua, attribute_names=["achievement"])

        if not ua.unlocked_at:
            ua.unlocked_at = datetime.utcnow()

        return ua

    async def check_unlock_conditions(self, db: AsyncSession, user_id: int, context: dict):
        """
        実績の解放条件をチェックし、条件を満たせば解放する
        context: {"type": "event_name", "value": int, ...}
        """
        event_type = context.get("type")
        value = context.get("value", 1)

        # 1. 該当するタイプの実績を取得
        stmt = select(Achievement)
        result = await db.execute(stmt)
        all_achievements = result.scalars().all()
        target_achievements = [a for a in all_achievements if a.conditions.get("type") == event_type]

        if not target_achievements:
            return

        # 2. ユーザーの実績状況を一括取得 (N+1回避)
        stmt_ua = select(UserAchievement).where(UserAchievement.user_id == user_id)
        result_ua = await db.execute(stmt_ua)
        user_achievements = result_ua.scalars().all()
        ua_map = {ua.achievement_id: ua for ua in user_achievements}

        for ach in target_achievements:
            ua = ua_map.get(ach.id)

            if not ua:
                ua = UserAchievement(
                    user_id=user_id,
                    achievement_id=ach.id,
                    progress={"current": 0}
                )
                db.add(ua)
                await db.flush()

            if ua.unlocked_at:
                continue

            # 進捗更新
            current_val = ua.progress.get("current", 0)
            new_val = current_val + value
            ua.progress = {"current": new_val} # dictを再代入して更新検知させる

            # 条件達成チェック
            target = ach.conditions.get("target", 0)
            if new_val >= target:
                ua.unlocked_at = datetime.utcnow()

    async def calculate_completion_rate(self, db: AsyncSession, user_id: int) -> float:
        """
        実績の達成率（％）を計算する
        """
        # 全実績数
        total_stmt = select(func.count(Achievement.id))
        total_res = await db.execute(total_stmt)
        total = total_res.scalar() or 0

        if total == 0:
            return 0.0

        # 解放済み実績数
        unlocked_stmt = select(func.count(UserAchievement.id)).where(
            UserAchievement.user_id == user_id,
            UserAchievement.unlocked_at.is_not(None)
        )
        unlocked_res = await db.execute(unlocked_stmt)
        unlocked = unlocked_res.scalar() or 0

        return (unlocked / total) * 100.0

    # --- イベントフック ---

    async def on_gacha_pull(self, db: AsyncSession, user_id: int, pull_count: int):
        """ガチャを引いた時に呼ばれるフック"""
        context = {"type": "gacha_pull", "value": pull_count}
        await self.check_unlock_conditions(db, user_id, context)

    async def on_pvp_win(self, db: AsyncSession, user_id: int):
        """PvPで勝利した時に呼ばれるフック"""
        context = {"type": "pvp_win", "value": 1}
        await self.check_unlock_conditions(db, user_id, context)

    async def on_quest_complete(self, db: AsyncSession, user_id: int):
        """クエストをクリアした時に呼ばれるフック"""
        context = {"type": "quest_complete", "value": 1}
        await self.check_unlock_conditions(db, user_id, context)

achievement_service = AchievementService()
