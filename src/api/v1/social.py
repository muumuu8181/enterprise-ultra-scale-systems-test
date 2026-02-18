from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from datetime import datetime

from src.database import get_db
from src.deps import get_current_user_id
from src.models.user import User
from src.models.social_models import FriendRequest, Friendship, Gift, FriendRequestStatus
from src.schemas import (
    FriendRequestCreate, FriendRequestResponse, FriendResponse,
    GiftSendRequest, GiftResponse, FeedItem
)

router = APIRouter()

@router.post("/friends/request", response_model=FriendRequestResponse)
async def send_friend_request(
    request: FriendRequestCreate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_id == request.target_user_id:
        raise HTTPException(status_code=400, detail="Cannot add self as friend")

    target_user = await db.get(User, request.target_user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check existing friendship
    existing_friendship = await db.execute(
        select(Friendship).where(
            or_(
                and_(Friendship.user1_id == user_id, Friendship.user2_id == request.target_user_id),
                and_(Friendship.user1_id == request.target_user_id, Friendship.user2_id == user_id)
            )
        )
    )
    if existing_friendship.scalars().first():
        raise HTTPException(status_code=400, detail="Already friends")

    # Check existing request
    existing_request = await db.execute(
        select(FriendRequest).where(
            or_(
                and_(FriendRequest.from_user_id == user_id, FriendRequest.to_user_id == request.target_user_id, FriendRequest.status == FriendRequestStatus.PENDING),
                and_(FriendRequest.from_user_id == request.target_user_id, FriendRequest.to_user_id == user_id, FriendRequest.status == FriendRequestStatus.PENDING)
            )
        )
    )
    if existing_request.scalars().first():
        raise HTTPException(status_code=400, detail="Friend request already pending")

    new_request = FriendRequest(
        from_user_id=user_id,
        to_user_id=request.target_user_id,
        status=FriendRequestStatus.PENDING
    )
    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)
    return new_request

@router.put("/friends/request/{id}/accept", response_model=FriendRequestResponse)
async def accept_friend_request(
    id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    req = await db.get(FriendRequest, id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.to_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to accept this request")

    if req.status != FriendRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is not pending")

    req.status = FriendRequestStatus.ACCEPTED

    # Create friendship (ordered)
    u1, u2 = sorted([req.from_user_id, req.to_user_id])
    friendship = Friendship(user1_id=u1, user2_id=u2)
    db.add(friendship)

    await db.commit()
    await db.refresh(req)
    return req

@router.delete("/friends/{id}")
async def delete_friend(
    id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Depending on interpretation, id is Friendship ID or Friend User ID.
    # Assuming Friendship ID based on REST conventions.

    friendship = await db.get(Friendship, id)
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")

    if friendship.user1_id != user_id and friendship.user2_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.delete(friendship)
    await db.commit()
    return {"message": "Friend removed"}

@router.get("/friends/{user_id}", response_model=List[FriendResponse])
async def list_friends(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Query friendships where user is involved
    result = await db.execute(
        select(Friendship).where(
            or_(Friendship.user1_id == user_id, Friendship.user2_id == user_id)
        )
    )
    friendships = result.scalars().all()

    friend_ids = []
    for f in friendships:
        if f.user1_id == user_id:
            friend_ids.append(f.user2_id)
        else:
            friend_ids.append(f.user1_id)

    if not friend_ids:
        return []

    # Fetch user details
    users_result = await db.execute(select(User).where(User.id.in_(friend_ids)))
    users_map = {u.id: u for u in users_result.scalars().all()}

    response = []
    for f in friendships:
        fid = f.user2_id if f.user1_id == user_id else f.user1_id
        if fid in users_map:
            response.append(FriendResponse(
                id=f.id,
                user_id=fid,
                name=users_map[fid].name,
                created_at=f.created_at
            ))

    return response

@router.post("/gifts/send", response_model=GiftResponse)
async def send_gift(
    request: GiftSendRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_id == request.friend_id:
        raise HTTPException(status_code=400, detail="Cannot gift self")

    # Verify friendship
    stmt = select(Friendship).where(
        or_(
            and_(Friendship.user1_id == user_id, Friendship.user2_id == request.friend_id),
            and_(Friendship.user1_id == request.friend_id, Friendship.user2_id == user_id)
        )
    )
    result = await db.execute(stmt)
    if not result.scalars().first():
        raise HTTPException(status_code=400, detail="Not friends")

    gift = Gift(
        from_user_id=user_id,
        to_user_id=request.friend_id,
        item_id=request.item_id,
        message=request.message,
        sent_at=datetime.utcnow()
    )
    db.add(gift)
    await db.commit()
    await db.refresh(gift)
    return gift

@router.get("/feed/{user_id}", response_model=List[FeedItem])
async def get_feed(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    feed = []

    # Recent gifts received
    gifts_res = await db.execute(
        select(Gift).where(Gift.to_user_id == user_id).order_by(Gift.sent_at.desc()).limit(10)
    )
    for g in gifts_res.scalars().all():
        feed.append(FeedItem(
            type="gift_received",
            content=f"Received gift {g.item_id} from user {g.from_user_id}",
            created_at=g.sent_at
        ))

    # Recent friends
    friends_res = await db.execute(
        select(Friendship).where(
            or_(Friendship.user1_id == user_id, Friendship.user2_id == user_id)
        ).order_by(Friendship.created_at.desc()).limit(10)
    )
    for f in friends_res.scalars().all():
        fid = f.user2_id if f.user1_id == user_id else f.user1_id
        feed.append(FeedItem(
            type="friend_added",
            content=f"Became friends with user {fid}",
            created_at=f.created_at
        ))

    feed.sort(key=lambda x: x.created_at, reverse=True)
    return feed
