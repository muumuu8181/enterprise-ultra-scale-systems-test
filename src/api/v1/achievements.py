from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.deps import get_current_user_id
from src.services.achievement_service import achievement_service
from src.schemas import AchievementResponse, UserAchievementResponse, UnlockRequest

router = APIRouter()

@router.get("/", response_model=List[AchievementResponse])
async def get_achievements(db: Annotated[AsyncSession, Depends(get_db)]):
    """
    全実績定義を取得する
    """
    return await achievement_service.get_all_achievements(db)

@router.get("/user/{user_id}", response_model=List[UserAchievementResponse])
async def get_user_achievements(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    指定ユーザーの獲得済み実績を取得する
    """
    return await achievement_service.get_user_achievements(db, user_id)

@router.post("/{achievement_id}/unlock", response_model=UserAchievementResponse)
async def unlock_achievement_endpoint(
    achievement_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    実績を手動で解放する（デバッグ・管理者用）
    """
    ua = await achievement_service.unlock_achievement(db, user_id, achievement_id)
    await db.commit()
    return ua
