from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import func
from src.models.loyalty_models import LoyaltyMember, PointsTransaction, TransactionType, TierLevel, LoyaltyTier

class PointsEarned(BaseModel):
    member_id: int
    points_earned: int
    new_balance: int
    tier: TierLevel

class RedemptionResult(BaseModel):
    success: bool
    message: str
    new_balance: int
    transaction_id: Optional[int] = None

async def earn_points(
    db: AsyncSession,
    member_id: int,
    purchase_amount: float,
    merchant_id: str
) -> PointsEarned:
    # 1. Get Member
    stmt = select(LoyaltyMember).where(LoyaltyMember.id == member_id)
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()

    if not member:
        raise ValueError(f"Member with id {member_id} not found")

    # 2. Get Tier Multiplier
    # Assuming tier info is in LoyaltyTier table.
    # If not found, default to 1.0 (Bronze default)
    tier_stmt = select(LoyaltyTier).where(LoyaltyTier.program_id == member.program_id, LoyaltyTier.tier_name == member.tier)
    tier_result = await db.execute(tier_stmt)
    tier_config = tier_result.scalar_one_or_none()

    multiplier = tier_config.multiplier if tier_config else 1.0

    # 3. Calculate Points
    # Base points: 1 point per unit of currency (simplified)
    points = int(purchase_amount * multiplier)

    # 4. Update Member
    member.points_balance += points
    member.lifetime_points += points

    # 5. Check for Tier Upgrade
    # Logic to check if lifetime_points qualifies for next tier
    # This requires querying all tiers for the program
    all_tiers_stmt = select(LoyaltyTier).where(LoyaltyTier.program_id == member.program_id).order_by(LoyaltyTier.min_points.asc())
    all_tiers_res = await db.execute(all_tiers_stmt)
    all_tiers = all_tiers_res.scalars().all()

    new_tier = member.tier
    for t in all_tiers:
        if member.lifetime_points >= t.min_points:
            new_tier = t.tier_name

    if new_tier != member.tier:
        member.tier = new_tier

    # 6. Record Transaction
    transaction = PointsTransaction(
        member_id=member.id,
        transaction_type=TransactionType.EARN,
        points=points,
        reference_id=f"PURCHASE:{merchant_id}",
        timestamp=datetime.now(timezone.utc)
    )
    db.add(transaction)

    await db.commit()
    await db.refresh(member)

    return PointsEarned(
        member_id=member.id,
        points_earned=points,
        new_balance=member.points_balance,
        tier=member.tier
    )

async def redeem_points(
    db: AsyncSession,
    member_id: int,
    reward_id: str,
    points_to_use: int
) -> RedemptionResult:
    # 1. Get Member
    stmt = select(LoyaltyMember).where(LoyaltyMember.id == member_id)
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()

    if not member:
        return RedemptionResult(success=False, message="Member not found", new_balance=0)

    # 2. Check Balance
    if member.points_balance < points_to_use:
        return RedemptionResult(success=False, message="Insufficient points", new_balance=member.points_balance)

    # 3. Deduct Points
    member.points_balance -= points_to_use

    # 4. Record Transaction
    transaction = PointsTransaction(
        member_id=member.id,
        transaction_type=TransactionType.REDEEM,
        points=-points_to_use,
        reference_id=f"REWARD:{reward_id}",
        timestamp=datetime.now(timezone.utc)
    )
    db.add(transaction)

    await db.commit()
    await db.refresh(transaction)

    return RedemptionResult(
        success=True,
        message="Redemption successful",
        new_balance=member.points_balance,
        transaction_id=transaction.id
    )

async def expire_stale_points(db: AsyncSession, days_inactive: int):
    # Logic: Find members who haven't had activity in X days and expire their points?
    # Or find points transactions older than X days that haven't been redeemed?
    # Usually "expire stale points" means expire points that are too old.
    # But usually it's based on "last activity".

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_inactive)

    # Simple logic: If last transaction was before cutoff_date, expire all points.
    # We need to query members and their last transaction date.

    # This is a potentially heavy query.
    # Strategy: Find members with points_balance > 0
    # For each, check last transaction timestamp.

    # Efficient way:
    # Subquery: Max timestamp per member
    subquery = (
        select(PointsTransaction.member_id, func.max(PointsTransaction.timestamp).label("last_activity"))
        .group_by(PointsTransaction.member_id)
        .subquery()
    )

    # Join Member with Subquery
    stmt = (
        select(LoyaltyMember)
        .outerjoin(subquery, LoyaltyMember.id == subquery.c.member_id)
        .where(
            LoyaltyMember.points_balance > 0,
            (subquery.c.last_activity < cutoff_date) | (subquery.c.last_activity == None)
        )
    )

    result = await db.execute(stmt)
    stale_members = result.scalars().all()

    expired_count = 0
    for member in stale_members:
        points_to_expire = member.points_balance
        if points_to_expire > 0:
            member.points_balance = 0

            transaction = PointsTransaction(
                member_id=member.id,
                transaction_type=TransactionType.EXPIRE,
                points=-points_to_expire,
                reference_id="EXPIRATION",
                timestamp=datetime.now(timezone.utc)
            )
            db.add(transaction)
            expired_count += 1

    await db.commit()
    return expired_count
