from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict

from src.database import get_db
from src.deps import get_current_user_id
from src.models.quest_models import Quest, UserQuest, QuestType, QuestStatus
from src.services.quest_service import QuestService

router = APIRouter()

# Pydantic Models
class QuestResponse(BaseModel):
    id: int
    type: str
    title: str
    description: Optional[str] = None
    conditions: Dict[str, Any]
    rewards: Dict[str, Any]
    status: str = QuestStatus.INACTIVE
    progress: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)

class QuestProgressRequest(BaseModel):
    increment: int = 1

class QuestCompleteResponse(BaseModel):
    success: bool
    rewards: Dict[str, Any]

@router.get("/daily", response_model=List[QuestResponse])
async def get_daily_quests(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Quest, UserQuest)
        .outerjoin(UserQuest, (Quest.id == UserQuest.quest_id) & (UserQuest.user_id == user_id))
        .where(Quest.type == QuestType.DAILY)
    )
    result = await db.execute(stmt)
    rows = result.all()

    response = []
    for quest, user_quest in rows:
        q_dict = {
            "id": quest.id,
            "type": quest.type.value if hasattr(quest.type, 'value') else quest.type,
            "title": quest.title,
            "description": quest.description,
            "conditions": quest.conditions,
            "rewards": quest.rewards,
            "status": user_quest.status if user_quest else QuestStatus.INACTIVE,
            "progress": user_quest.progress if user_quest else {}
        }
        response.append(QuestResponse(**q_dict))

    return response

@router.get("/weekly", response_model=List[QuestResponse])
async def get_weekly_quests(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Quest, UserQuest)
        .outerjoin(UserQuest, (Quest.id == UserQuest.quest_id) & (UserQuest.user_id == user_id))
        .where(Quest.type == QuestType.WEEKLY)
    )
    result = await db.execute(stmt)
    rows = result.all()

    response = []
    for quest, user_quest in rows:
        q_dict = {
            "id": quest.id,
            "type": quest.type.value if hasattr(quest.type, 'value') else quest.type,
            "title": quest.title,
            "description": quest.description,
            "conditions": quest.conditions,
            "rewards": quest.rewards,
            "status": user_quest.status if user_quest else QuestStatus.INACTIVE,
            "progress": user_quest.progress if user_quest else {}
        }
        response.append(QuestResponse(**q_dict))

    return response

@router.post("/{quest_id}/accept", response_model=QuestResponse)
async def accept_quest(
    quest_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    quest = await db.get(Quest, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    result = await db.execute(select(UserQuest).where(UserQuest.user_id == user_id, UserQuest.quest_id == quest_id))
    user_quest = result.scalars().first()

    if user_quest:
        if user_quest.status != QuestStatus.INACTIVE:
             raise HTTPException(status_code=400, detail="Quest already active or completed")
        # Reactivate
        user_quest.status = QuestStatus.ACCEPTED
        user_quest.accepted_at = datetime.utcnow()
        user_quest.progress = {"current_count": 0}
        user_quest.completed_at = None
    else:
        user_quest = UserQuest(
            user_id=user_id,
            quest_id=quest_id,
            status=QuestStatus.ACCEPTED,
            accepted_at=datetime.utcnow(),
            progress={"current_count": 0}
        )
        db.add(user_quest)

    await db.commit()
    await db.refresh(user_quest)
    await db.refresh(quest)

    return QuestResponse(
        id=quest.id,
        type=quest.type.value if hasattr(quest.type, 'value') else quest.type,
        title=quest.title,
        description=quest.description,
        conditions=quest.conditions,
        rewards=quest.rewards,
        status=user_quest.status,
        progress=user_quest.progress
    )

@router.post("/{quest_id}/progress", response_model=QuestResponse)
async def progress_quest(
    quest_id: int,
    request: QuestProgressRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    uq = await QuestService.track_progress(user_id, quest_id, request.increment, db)
    if not uq:
         raise HTTPException(status_code=400, detail="Quest not active or not found")

    quest = await db.get(Quest, quest_id)

    return QuestResponse(
        id=quest.id,
        type=quest.type.value if hasattr(quest.type, 'value') else quest.type,
        title=quest.title,
        description=quest.description,
        conditions=quest.conditions,
        rewards=quest.rewards,
        status=uq.status,
        progress=uq.progress
    )

@router.post("/{quest_id}/complete", response_model=QuestCompleteResponse)
async def complete_quest(
    quest_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserQuest).where(UserQuest.user_id == user_id, UserQuest.quest_id == quest_id))
    user_quest = result.scalars().first()

    if not user_quest:
        raise HTTPException(status_code=404, detail="User quest not found")

    if user_quest.status == QuestStatus.CLAIMED:
        raise HTTPException(status_code=400, detail="Reward already claimed")

    if user_quest.status != QuestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Quest not completed yet")

    quest = await db.get(Quest, quest_id)
    rewards = quest.rewards

    await QuestService.grant_rewards(user_id, rewards, db)

    user_quest.status = QuestStatus.CLAIMED
    await db.commit()

    return QuestCompleteResponse(
        success=True,
        rewards=rewards
    )
