from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from redis.asyncio import Redis

from src.database import get_db
from src.deps import get_redis, get_current_user_id
from src.models.purchase import Purchase
from src.models.user import User
from src.schemas import PurchaseVerifyRequest, PurchaseVerifyResponse

router = APIRouter()

@router.post("/verify", response_model=PurchaseVerifyResponse)
async def verify_purchase(
    request: PurchaseVerifyRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    # 0. Acquire Lock to prevent race conditions
    lock_key = f"lock:receipt:{request.receipt_id}"
    is_locked = await redis.set(lock_key, "locked", nx=True, ex=30) # 30s lock
    if not is_locked:
        # Check if already processed (idempotency check handles this, but here we might just wait or error)
        # For simplicity, returning 409
        raise HTTPException(status_code=409, detail="Receipt verification in progress")

    try:
        # 1. Check for Duplicate Receipt (DB Check)
        stmt = select(Purchase).where(Purchase.receipt_id == request.receipt_id)
        result = await db.execute(stmt)
        existing = result.scalars().first()
        if existing:
            # Idempotency: if already processed, return success but don't add currency again
            if existing.verified:
                 current_balance = await redis.get(f"user:{user_id}:currency")
                 return PurchaseVerifyResponse(
                     success=True,
                     currency_added=0,
                     current_balance=int(current_balance) if current_balance else 0
                 )
            else:
                 raise HTTPException(status_code=400, detail="Receipt already processed/invalid")

        # 2. Verify Receipt (Mock)
        # In real app, call Apple/Google API
        verified = True
        if not verified:
            raise HTTPException(status_code=400, detail="Invalid receipt")

        # 3. Add Currency
        currency_to_add = request.currency_to_add

        # DB Record
        purchase = Purchase(
            user_id=user_id,
            amount=request.amount,
            currency_added=currency_to_add,
            receipt_id=request.receipt_id,
            verified=verified
        )
        db.add(purchase)

        # Redis Update
        user_currency_key = f"user:{user_id}:currency"
        new_balance = await redis.incrby(user_currency_key, currency_to_add)

        # DB Sync
        await db.execute(update(User).where(User.id == user_id).values(currency=User.currency + currency_to_add))

        await db.commit()

        return PurchaseVerifyResponse(
            success=True,
            currency_added=currency_to_add,
            current_balance=new_balance
        )
    finally:
        # Release Lock
        await redis.delete(lock_key)
