from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict

from src.models.platooning_models import PlatoonGroup, PlatoonMember
from src.services.platoon_controller import PlatoonController

router = APIRouter(prefix="/platooning", tags=["platooning"])

# Dependency
async def get_db():
    yield None

controller = PlatoonController()

# Schemas
class CreateGroupRequest(BaseModel):
    leader_vehicle_id: str
    max_members: int
    target_speed: float
    spacing_distance: float = 10.0

class JoinGroupRequest(BaseModel):
    vehicle_id: str
    position: int

class CommandRequest(BaseModel):
    action: str # accelerate, brake, dissolve

class PlatoonGroupResponse(BaseModel):
    id: int
    leader_id: str
    status: str
    target_speed: float
    spacing_distance: float
    member_count: int

    model_config = ConfigDict(from_attributes=True)

class PlatoonMemberResponse(BaseModel):
    id: int
    group_id: int
    vehicle_id: str
    position_in_platoon: int

    model_config = ConfigDict(from_attributes=True)

class GroupStatusResponse(BaseModel):
    group: PlatoonGroupResponse
    members: List[PlatoonMemberResponse]

@router.post("/groups", response_model=PlatoonGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    req: CreateGroupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    新規隊列を作成する。
    Create a new platoon group.
    """
    if not db:
        # Mock behavior if DB is missing (though in tests we might provide it)
        # But for now raising 503 is safer if logic depends on DB
        raise HTTPException(status_code=503, detail="Database not available")

    group = await controller.form_platoon(
        db,
        leader_id=req.leader_vehicle_id,
        max_members=req.max_members,
        target_speed=req.target_speed,
        spacing_distance=req.spacing_distance
    )
    return group

@router.post("/groups/{id}/join", response_model=PlatoonMemberResponse)
async def join_group(
    id: int = Path(...),
    req: JoinGroupRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    隊列に参加する。
    Join an existing platoon.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    member = await controller.join_platoon(
        db,
        group_id=id,
        vehicle_id=req.vehicle_id,
        position=req.position
    )
    if not member:
        raise HTTPException(status_code=404, detail="Group not found or join failed")
    return member

@router.delete("/groups/{id}/leave")
async def leave_group(
    id: int = Path(...),
    vehicle_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    隊列から離脱する。
    Leave a platoon.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    success = await controller.leave_platoon(db, group_id=id, vehicle_id=vehicle_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member or Group not found")

    return {"status": "left"}

@router.get("/groups/{id}/status", response_model=GroupStatusResponse)
async def get_group_status(
    id: int = Path(...),
    db: AsyncSession = Depends(get_db)
):
    """
    隊列の状態を取得する。
    Get platoon status.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    # Fetch group
    result = await db.execute(select(PlatoonGroup).where(PlatoonGroup.id == id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Fetch members
    res_members = await db.execute(select(PlatoonMember).where(PlatoonMember.group_id == id))
    members = res_members.scalars().all()

    return GroupStatusResponse(group=group, members=members)

@router.put("/groups/{id}/command")
async def command_group(
    id: int = Path(...),
    req: CommandRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    隊列にコマンドを送信する。
    Send command to platoon.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    if req.action == "accelerate":
        # Placeholder for acceleration logic
        # Could update target_speed in future
        pass
    elif req.action == "brake":
        await controller.handle_emergency_brake(db, id)
    elif req.action == "dissolve":
        success = await controller.dissolve_platoon(db, id)
        if not success:
             raise HTTPException(status_code=404, detail="Group not found")
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    return {"status": "command_sent", "action": req.action}
