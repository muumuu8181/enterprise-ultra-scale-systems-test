from typing import List, Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from redis.asyncio import Redis

from src.database import get_db
from src.deps import get_redis, get_current_user_id
from src.models.gacha import GachaBanner, GachaRate, GachaLog, UserPityCounter
from src.models.user import User
from src.schemas import GachaPullRequest, GachaPullResponse, GachaBannerResponse, GachaLogResponse, GachaResultItem
from src.services.gacha_service import GachaService

router = APIRouter()

@router.post("/pull", response_model=GachaPullResponse)
async def gacha_pull(
    request: GachaPullRequest,
    x_request_id: Annotated[str, Header()],
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    # 1. Idempotency Check (Redis)
    idempotency_key = f"gacha:req:{x_request_id}"
    if await redis.exists(idempotency_key):
        # Could return cached response if stored
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate request")

    # 2. Validate Banner
    banner = await db.get(GachaBanner, request.banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    # Fetch Rates
    result = await db.execute(select(GachaRate).where(GachaRate.banner_id == request.banner_id))
    rates = result.scalars().all()
    if not rates:
        raise HTTPException(status_code=500, detail="Banner has no rates configured")

    # 3. Check Currency (Redis + DB Sync check ideally)
    cost = 100 * request.count  # Assuming 100 per pull
    user_currency_key = f"user:{user_id}:currency"

    # Retry loop for Redis watch
    max_retries = 3
    for _ in range(max_retries):
        try:
            async with redis.pipeline(transaction=True) as pipe:
                await pipe.watch(user_currency_key)
                current_balance = await pipe.get(user_currency_key)

                if current_balance is None:
                    # Key missing, fetch from DB
                    # Unwatch first to avoid blocking others if DB is slow?
                    # But we need atomicity. Actually, standard pattern is to break, set, retry.
                    await pipe.unwatch()
                    user_obj = await db.get(User, user_id)
                    if not user_obj:
                         raise HTTPException(status_code=404, detail="User not found")
                    # Set initial value to Redis
                    await redis.set(user_currency_key, user_obj.currency)
                    continue # Retry loop

                current_balance = int(current_balance)
                if current_balance < cost:
                    await pipe.unwatch()
                    raise HTTPException(status_code=400, detail="Insufficient currency")

                pipe.multi()
                pipe.decrby(user_currency_key, cost)
                pipe.setex(idempotency_key, 60, "processed") # TTL 60s
                await pipe.execute()
                break # Success
        except Exception as e:
            # WatchError (if concurrent modification) or other Redis error
            # If watch failed, retry
            # If explicit exception raised above, re-raise
            if isinstance(e, HTTPException):
                raise e
            # Log error and retry if it's a WatchError (redis-py raises WatchError on execute usually)
            # But redis-py async pipeline might raise it differently.
            # Assuming general retry for optimistic locking failure.
            continue
    else:
        raise HTTPException(status_code=500, detail="Transaction failed after retries")

    # 4. Gacha Logic
    # Get Pity
    # We lock user pity row for update? Or assume single user request sequentiality
    # For now, just fetch
    pity_record = await db.get(UserPityCounter, (user_id, banner.pool_type))
    current_pity = pity_record.pity_count if pity_record else 0

    results, new_pity = GachaService.simulate_pulls(rates, request.count, current_pity)

    # 5. Persist Results (DB Transaction)
    # Update Pity
    if pity_record:
        pity_record.pity_count = new_pity
        # pity_record.updated_at automatic
    else:
        new_record = UserPityCounter(user_id=user_id, pool_type=banner.pool_type, pity_count=new_pity)
        db.add(new_record)

    # Insert Logs
    log_entries = []
    for item in results:
        log_entries.append(GachaLog(
            user_id=user_id,
            banner_id=request.banner_id,
            item_id=item['item_id'],
            rarity=item['rarity']
        ))
    db.add_all(log_entries)

    # Deduct DB Currency to keep in sync
    await db.execute(update(User).where(User.id == user_id).values(currency=User.currency - cost))

    await db.commit()

    return GachaPullResponse(
        results=[GachaResultItem(**r) for r in results],
        currency_remaining=current_balance - cost
    )

@router.get("/banners", response_model=List[GachaBannerResponse])
async def get_banners(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(GachaBanner))
    banners = result.scalars().all()
    return banners

@router.get("/history", response_model=List[GachaLogResponse])
async def get_history(
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    limit: int = 10
):
    offset = (page - 1) * limit
    result = await db.execute(
        select(GachaLog)
        .where(GachaLog.user_id == user_id)
        .order_by(GachaLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    logs = result.scalars().all()
    return logs
