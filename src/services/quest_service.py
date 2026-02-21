from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.models.quest_models import Quest, UserQuest, QuestType, QuestStatus
from src.models.user import User

class QuestService:
    @staticmethod
    async def reset_daily_quests(db: AsyncSession):
        """
        Resets all UserQuest entries for daily quests to INACTIVE.
        This allows users to re-accept daily quests.
        """
        result = await db.execute(select(Quest.id).where(Quest.type == QuestType.DAILY))
        daily_ids = result.scalars().all()

        if not daily_ids:
            return

        # Reset all UserQuests for these quests to INACTIVE
        # This effectively wipes the state allowing re-take
        await db.execute(
            update(UserQuest)
            .where(UserQuest.quest_id.in_(daily_ids))
            .values(
                status=QuestStatus.INACTIVE,
                progress={},
                accepted_at=None,
                completed_at=None
            )
        )
        await db.commit()

    @staticmethod
    def check_completion_conditions(quest: Quest, progress: dict) -> bool:
        """
        Checks if the current progress satisfies the quest conditions.
        Assumes condition schema: {"target_count": int}
        Assumes progress schema: {"current_count": int}
        """
        conditions = quest.conditions
        if not conditions:
            return True

        target = conditions.get("target_count")
        if target is not None:
            current = progress.get("current_count", 0)
            return current >= target

        return False

    @staticmethod
    async def grant_rewards(user_id: int, rewards: dict, db: AsyncSession):
        """
        Grants rewards to the user.
        Supported rewards: "currency" (int)
        """
        currency = rewards.get("currency")
        if currency:
            user = await db.get(User, user_id)
            if user:
                user.currency += currency
                # Session will handle commit when flushed/committed by caller or this method

    @staticmethod
    async def track_progress(user_id: int, quest_id: int, increment: int, db: AsyncSession):
        """
        Increments progress for a user's active quest.
        """
        result = await db.execute(
            select(UserQuest).where(
                UserQuest.user_id == user_id,
                UserQuest.quest_id == quest_id,
                UserQuest.status == QuestStatus.ACCEPTED
            )
        )
        uq = result.scalars().first()
        if not uq:
            return None

        # Update progress
        new_progress = dict(uq.progress) if uq.progress else {}
        current_val = new_progress.get("current_count", 0)
        new_progress["current_count"] = current_val + increment
        uq.progress = new_progress

        # Check completion
        quest = await db.get(Quest, quest_id)
        if QuestService.check_completion_conditions(quest, new_progress):
            uq.status = QuestStatus.COMPLETED
            uq.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(uq)
        return uq
