from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Any

from src.models.loyalty_models import LoyaltyMember, PointsTransaction, TierLevel, LoyaltyTier
from src.services.points_service import earn_points, redeem_points, PointsEarned, RedemptionResult

router = APIRouter()

# Placeholder dependency - normally imported from src.db.session
async def get_db():
    # In a real app, this would yield a session from a sessionmaker
    raise NotImplementedError("Database session dependency not implemented")

# Request Models
class EnrollRequest(BaseModel):
    user_id: str
    program_id: str

class EarnPointsRequest(BaseModel):
    member_id: int
    purchase_amount: float
    merchant_id: str

class RedeemPointsRequest(BaseModel):
    reward_id: str
    points_to_use: int

# Response Models
class MemberResponse(BaseModel):
    id: int
    user_id: str
    program_id: str
    tier: TierLevel
    points_balance: int
    lifetime_points: int

    class Config:
        from_attributes = True

class PointsTransactionResponse(BaseModel):
    id: int
    transaction_type: str
    points: int
    reference_id: Optional[str]
    timestamp: Any

    class Config:
        from_attributes = True

class TierProgressResponse(BaseModel):
    current_tier: TierLevel
    next_tier: Optional[str]
    points_needed: int
    current_lifetime_points: int

class RewardItem(BaseModel):
    id: str
    name: str
    points_cost: int
    description: str

# Endpoints

@router.post("/members/enroll", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def enroll_member(request: EnrollRequest, db: AsyncSession = Depends(get_db)):
    # Check if already enrolled? (omitted for brevity, assuming new)
    new_member = LoyaltyMember(
        user_id=request.user_id,
        program_id=request.program_id,
        tier=TierLevel.BRONZE,
        points_balance=0,
        lifetime_points=0
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    return new_member

@router.get("/members/{member_id}/points-statement", response_model=List[PointsTransactionResponse])
async def get_points_statement(member_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(PointsTransaction).where(PointsTransaction.member_id == member_id).order_by(PointsTransaction.timestamp.desc())
    result = await db.execute(stmt)
    transactions = result.scalars().all()
    return transactions

@router.get("/members/{member_id}/tier-progress", response_model=TierProgressResponse)
async def get_tier_progress(member_id: int, db: AsyncSession = Depends(get_db)):
    member_stmt = select(LoyaltyMember).where(LoyaltyMember.id == member_id)
    result = await db.execute(member_stmt)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Get next tier
    # Assume tiers are ordered by min_points
    tiers_stmt = select(LoyaltyTier).where(LoyaltyTier.program_id == member.program_id).order_by(LoyaltyTier.min_points.asc())
    tiers_res = await db.execute(tiers_stmt)
    all_tiers = tiers_res.scalars().all()

    next_tier = None
    points_needed = 0

    current_min = 0
    # Find current tier index and look ahead?
    # Or just find the first tier with min_points > lifetime_points?
    # No, tier is based on lifetime_points usually.

    # Logic: Find the lowest tier with min_points > member.lifetime_points
    for t in all_tiers:
        if t.min_points > member.lifetime_points:
            next_tier = t.tier_name
            points_needed = t.min_points - member.lifetime_points
            break

    return TierProgressResponse(
        current_tier=member.tier,
        next_tier=next_tier,
        points_needed=points_needed,
        current_lifetime_points=member.lifetime_points
    )

@router.post("/members/{member_id}/redeem", response_model=RedemptionResult)
async def redeem_points_endpoint(member_id: int, request: RedeemPointsRequest, db: AsyncSession = Depends(get_db)):
    result = await redeem_points(db, member_id, request.reward_id, request.points_to_use)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result

@router.get("/members/{member_id}/rewards-catalog", response_model=List[RewardItem])
async def get_rewards_catalog(member_id: int, db: AsyncSession = Depends(get_db)):
    # Mock catalog
    return [
        RewardItem(id="REW001", name="Gift Card $10", points_cost=1000, description="Amazon Gift Card"),
        RewardItem(id="REW002", name="Flight Upgrade", points_cost=5000, description="Upgrade to Business Class"),
        RewardItem(id="REW003", name="Coffee", points_cost=100, description="Free Coffee")
    ]

@router.post("/points/earn", response_model=PointsEarned)
async def earn_points_endpoint(request: EarnPointsRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await earn_points(db, request.member_id, request.purchase_amount, request.merchant_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
