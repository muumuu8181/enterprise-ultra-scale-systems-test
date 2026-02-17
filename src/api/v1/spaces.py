from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from src.database import get_db
from src.models.metaverse_models import VirtualSpace, Avatar, SpaceType
from src.services.spatial_service import SpatialService

router = APIRouter()

class CreateSpaceRequest(BaseModel):
    name: str
    owner_id: int
    max_occupancy: int = 100
    space_type: SpaceType = SpaceType.room

class JoinSpaceRequest(BaseModel):
    avatar_id: int
    user_id: int # Verification purpose
    initial_x: float = 0.0
    initial_y: float = 0.0
    initial_z: float = 0.0

class PlaceAssetRequest(BaseModel):
    asset_id: str
    position: Dict[str, float]
    scale: Dict[str, float]
    rotation: Dict[str, float]

class BroadcastEventRequest(BaseModel):
    event_type: str
    payload: Dict[str, Any]

@router.post("/create", response_model=Dict[str, Any])
async def create_space(request: CreateSpaceRequest, db: AsyncSession = Depends(get_db)):
    space = VirtualSpace(
        name=request.name,
        owner_id=request.owner_id,
        max_occupancy=request.max_occupancy,
        space_type=request.space_type
    )
    db.add(space)
    await db.commit()
    await db.refresh(space)
    return {"id": space.id, "name": space.name, "status": "created"}

@router.get("/{id}/occupants", response_model=List[Dict[str, Any]])
async def get_occupants(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Avatar).where(Avatar.current_space_id == id)
    result = await db.execute(stmt)
    avatars = result.scalars().all()
    return [{"id": a.id, "display_name": a.display_name, "position": {"x": a.position_x, "y": a.position_y, "z": a.position_z}} for a in avatars]

@router.post("/{id}/join")
async def join_space(id: int, request: JoinSpaceRequest, db: AsyncSession = Depends(get_db)):
    service = SpatialService(db)
    # Check if space exists
    stmt = select(VirtualSpace).where(VirtualSpace.id == id)
    result = await db.execute(stmt)
    space = result.scalar_one_or_none()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    # Check if avatar exists
    stmt_avatar = select(Avatar).where(Avatar.id == request.avatar_id)
    result_avatar = await db.execute(stmt_avatar)
    avatar = result_avatar.scalar_one_or_none()

    if not avatar:
        # Create avatar on the fly for demo
        stmt_user_avatar = select(Avatar).where(Avatar.user_id == request.user_id)
        result_user_avatar = await db.execute(stmt_user_avatar)
        avatar = result_user_avatar.scalar_one_or_none()

        if not avatar:
             avatar = Avatar(
                user_id=request.user_id,
                display_name=f"User_{request.user_id}",
                current_space_id=None # Initially None
             )
             db.add(avatar)
             await db.commit()
             await db.refresh(avatar)

    try:
        updated_avatar = await service.update_avatar_position(
            avatar.id,
            request.initial_x,
            request.initial_y,
            request.initial_z,
            id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated_avatar:
         raise HTTPException(status_code=404, detail="Avatar not found")

    return {"status": "joined", "space_id": id, "position": {"x": updated_avatar.position_x, "y": updated_avatar.position_y, "z": updated_avatar.position_z}}

@router.post("/{id}/broadcast-event")
async def broadcast_event(id: int, request: BroadcastEventRequest, db: AsyncSession = Depends(get_db)):
    # In a real system, this would push to a pub/sub (Redis/Kafka)
    # Here we just acknowledge
    return {"status": "broadcasted", "event_type": request.event_type, "target_space": id}

@router.get("/{id}/asset-manifest")
async def get_asset_manifest(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(VirtualSpace).where(VirtualSpace.id == id)
    result = await db.execute(stmt)
    space = result.scalar_one_or_none()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return space.asset_manifest

@router.post("/{id}/place-asset")
async def place_asset(id: int, request: PlaceAssetRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(VirtualSpace).where(VirtualSpace.id == id)
    result = await db.execute(stmt)
    space = result.scalar_one_or_none()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    # Simple JSON update
    # Ensure asset_manifest is a dict
    current_manifest = dict(space.asset_manifest) if space.asset_manifest else {}

    asset_entry = {
        "asset_id": request.asset_id,
        "position": request.position,
        "scale": request.scale,
        "rotation": request.rotation
    }

    if "placed_assets" not in current_manifest:
        current_manifest["placed_assets"] = []

    current_manifest["placed_assets"].append(asset_entry)

    space.asset_manifest = current_manifest

    await db.commit()
    await db.refresh(space)

    return {"status": "placed", "asset_count": len(current_manifest["placed_assets"])}
