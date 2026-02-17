from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.database import get_db
from src.deps import get_current_user_id
from src.models.guild_models import Guild, GuildMember, GuildBattle
from src.schemas import (
    GuildCreate,
    GuildResponse,
    GuildMemberResponse,
    GuildBattleCreate,
    GuildBattleResponse,
)

router = APIRouter()

@router.post("/", response_model=GuildResponse)
async def create_guild(
    guild_in: GuildCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    ギルドを作成する
    """
    # Check if name exists
    stmt = select(Guild).where(Guild.name == guild_in.name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guild name already exists",
        )

    # Check if user is already in a guild
    stmt = select(GuildMember).where(GuildMember.user_id == user_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already in a guild",
        )

    # Create Guild
    new_guild = Guild(
        name=guild_in.name,
        description=guild_in.description,
        leader_id=user_id,
        max_members=guild_in.max_members,
        members_count=1,
    )
    db.add(new_guild)
    await db.flush() # to get id

    # Add leader as member
    leader_member = GuildMember(
        guild_id=new_guild.id,
        user_id=user_id,
        role="leader",
    )
    db.add(leader_member)
    await db.commit()
    await db.refresh(new_guild)
    return new_guild

@router.get("/{guild_id}", response_model=GuildResponse)
async def get_guild(
    guild_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    ギルド情報を取得する
    """
    guild = await db.get(Guild, guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")
    return guild

@router.post("/{guild_id}/join", response_model=GuildMemberResponse)
async def join_guild(
    guild_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    ギルドに参加する
    """
    guild = await db.get(Guild, guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")

    if guild.members_count >= guild.max_members:
        raise HTTPException(status_code=400, detail="Guild is full")

    # Check if user is already in a guild
    stmt = select(GuildMember).where(GuildMember.user_id == user_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already in a guild")

    member = GuildMember(
        guild_id=guild_id,
        user_id=user_id,
        role="member",
    )
    db.add(member)

    # Update count
    guild.members_count += 1

    await db.commit()
    await db.refresh(member)
    return member

@router.delete("/{guild_id}/leave")
async def leave_guild(
    guild_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    ギルドから脱退する
    """
    # Check if member
    stmt = select(GuildMember).where(
        GuildMember.guild_id == guild_id,
        GuildMember.user_id == user_id
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=400, detail="Not a member of this guild")

    # Logic for leader leaving: strict prevent or disband?
    # Simple logic: prevent if leader
    if member.role == "leader":
         raise HTTPException(status_code=400, detail="Leader cannot leave. Promote another member or delete guild.")

    await db.delete(member)

    # Update count
    guild = await db.get(Guild, guild_id)
    if guild:
        guild.members_count -= 1

    await db.commit()
    return {"message": "Left guild successfully"}

@router.put("/{guild_id}/promote")
async def promote_member(
    guild_id: int,
    target_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    メンバーを副リーダーに昇格させる (リーダーのみ実行可能)
    """
    # Check if current user is leader
    stmt = select(GuildMember).where(
        GuildMember.guild_id == guild_id,
        GuildMember.user_id == current_user_id
    )
    result = await db.execute(stmt)
    current_member = result.scalar_one_or_none()

    if not current_member or current_member.role != "leader":
        raise HTTPException(status_code=403, detail="Only leader can promote")

    # Check target member
    stmt = select(GuildMember).where(
        GuildMember.guild_id == guild_id,
        GuildMember.user_id == target_user_id
    )
    result = await db.execute(stmt)
    target_member = result.scalar_one_or_none()

    if not target_member:
        raise HTTPException(status_code=404, detail="Target member not found")

    target_member.role = "vice_leader"
    await db.commit()
    return {"message": "Member promoted to vice_leader"}

@router.get("/{guild_id}/members", response_model=List[GuildMemberResponse])
async def list_members(
    guild_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    ギルドメンバー一覧を取得する
    """
    stmt = select(GuildMember).where(GuildMember.guild_id == guild_id)
    result = await db.execute(stmt)
    members = result.scalars().all()
    return members

@router.post("/{guild_id}/battle", response_model=GuildBattleResponse)
async def start_battle(
    guild_id: int,
    battle_in: GuildBattleCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    ギルドバトルを開始する
    """
    # Check permission (leader/vice_leader?)
    stmt = select(GuildMember).where(
        GuildMember.guild_id == guild_id,
        GuildMember.user_id == user_id
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()

    if not member or member.role not in ["leader", "vice_leader"]:
        raise HTTPException(status_code=403, detail="Only leader or vice_leader can start battle")

    # Check existence
    guild_a = await db.get(Guild, guild_id)
    guild_b = await db.get(Guild, battle_in.opponent_guild_id)

    if not guild_a or not guild_b:
        raise HTTPException(status_code=404, detail="Guild not found")

    if guild_id == battle_in.opponent_guild_id:
         raise HTTPException(status_code=400, detail="Cannot battle self")

    battle = GuildBattle(
        guild_a_id=guild_id,
        guild_b_id=battle_in.opponent_guild_id,
        # winner, ended_at are null initially
        # scores can be initialized
        scores={"guild_a": 0, "guild_b": 0}
    )
    db.add(battle)
    await db.commit()
    await db.refresh(battle)
    return battle
