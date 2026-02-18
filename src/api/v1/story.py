from typing import List, Optional, Dict, Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict

from src.database import get_db
from src.deps import get_current_user_id
from src.models.story_models import Chapter, Stage, UserStageProgress
from src.services.story_service import StoryService

router = APIRouter()

# Schemas
class ChapterResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    order: int
    unlock_conditions: Optional[Dict[str, Any]] = None
    rewards: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class StageResponse(BaseModel):
    id: int
    chapter_id: int
    title: str
    order: int
    difficulty: int
    recommended_power: int
    star_conditions: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class StageCompleteRequest(BaseModel):
    score: int
    time_sec: int

class UserStageProgressResponse(BaseModel):
    id: int
    user_id: int
    stage_id: int
    cleared: bool
    stars: int
    best_score: int
    attempts: int

    model_config = ConfigDict(from_attributes=True)

class UserProgressResponse(BaseModel):
    user_id: int
    progress: List[UserStageProgressResponse]

    model_config = ConfigDict(from_attributes=True)


# Endpoints

@router.get("/chapters", response_model=List[ChapterResponse])
async def get_chapters(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[int, Depends(get_current_user_id)]
):
    """
    章一覧を取得する。
    """
    result = await db.execute(select(Chapter).order_by(Chapter.order))
    chapters = result.scalars().all()
    return chapters

@router.get("/chapters/{chapter_id}/stages", response_model=List[StageResponse])
async def get_chapter_stages(
    chapter_id: Annotated[int, Path(title="Chapter ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[int, Depends(get_current_user_id)]
):
    """
    指定された章のステージ一覧を取得する。
    """
    # 章が存在するか確認
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # 解放状態チェック
    is_unlocked = await StoryService.unlock_chapter(user_id, chapter_id, db)
    if not is_unlocked:
        raise HTTPException(status_code=403, detail="Chapter is locked")

    result = await db.execute(select(Stage).where(Stage.chapter_id == chapter_id).order_by(Stage.order))
    stages = result.scalars().all()
    return stages

@router.post("/stages/{stage_id}/start")
async def start_stage(
    stage_id: Annotated[int, Path(title="Stage ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[int, Depends(get_current_user_id)]
):
    """
    ステージ開始処理。スタミナ消費などをここで行う想定。
    """
    stage = await db.get(Stage, stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    # 章解放チェック
    is_unlocked = await StoryService.unlock_chapter(user_id, stage.chapter_id, db)
    if not is_unlocked:
        raise HTTPException(status_code=403, detail="Chapter is locked")

    # TODO: スタミナ消費ロジック

    return {"message": "Stage started", "stage_id": stage_id}

@router.post("/stages/{stage_id}/complete", response_model=UserStageProgressResponse)
async def complete_stage_endpoint(
    stage_id: Annotated[int, Path(title="Stage ID")],
    request: Annotated[StageCompleteRequest, Body()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[int, Depends(get_current_user_id)]
):
    """
    ステージクリア処理。
    """
    # ステージ存在確認
    stage = await db.get(Stage, stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    # 章解放チェック
    is_unlocked = await StoryService.unlock_chapter(user_id, stage.chapter_id, db)
    if not is_unlocked:
        raise HTTPException(status_code=403, detail="Chapter is locked")

    try:
        progress = await StoryService.complete_stage(
            user_id, stage_id, request.score, request.time_sec, db
        )

        return progress
    except Exception as e:
        # DBエラーなども含めてキャッチ
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progress/{target_user_id}", response_model=UserProgressResponse)
async def get_user_progress(
    target_user_id: Annotated[int, Path(title="User ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)]
):
    """
    ユーザーの進捗を取得する。
    """
    stmt = select(UserStageProgress).where(UserStageProgress.user_id == target_user_id)
    result = await db.execute(stmt)
    progress_list = result.scalars().all()

    return UserProgressResponse(user_id=target_user_id, progress=progress_list)
