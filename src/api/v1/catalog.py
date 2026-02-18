from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from src.services import campaign_service
from src.services.campaign_service import PointsBonus

router = APIRouter()

# Response Models
class RewardSchema(BaseModel):
    id: int
    program_id: int
    name: str
    category: str
    points_cost: int
    inventory: int
    expiry: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AvailabilityResponse(BaseModel):
    reward_id: int
    available: bool
    inventory: int

class RedemptionRequest(BaseModel):
    member_id: int
    quantity: int = 1

class PartnerRedemptionOption(BaseModel):
    partner_id: int
    partner_name: str
    conversion_rate: float
    min_points: int

class TransactionRequest(BaseModel):
    member_id: int
    amount: float
    merchant_category: str
    timestamp: datetime

@router.get("/rewards/catalog", response_model=List[RewardSchema])
async def get_rewards_catalog():
    """
    Get the full catalog of rewards.
    """
    # Mock data
    return [
        RewardSchema(
            id=1,
            program_id=101,
            name="Weekend Getaway",
            category="travel",
            points_cost=5000,
            inventory=5,
            expiry=datetime(2024, 12, 31)
        )
    ]

@router.get("/rewards/{id}/availability", response_model=AvailabilityResponse)
async def check_reward_availability(id: int):
    """
    Check availability of a specific reward.
    """
    # Mock logic
    return AvailabilityResponse(reward_id=id, available=True, inventory=10)

@router.post("/rewards/{id}/request")
async def request_reward_redemption(id: int, request: RedemptionRequest):
    """
    Request redemption of a reward.
    """
    return {"status": "success", "message": f"Redemption request for reward {id} received for member {request.member_id}"}

@router.get("/partners/redemption-options", response_model=List[PartnerRedemptionOption])
async def get_partner_redemption_options():
    """
    Get available partner redemption options.
    """
    return [
        PartnerRedemptionOption(
            partner_id=1,
            partner_name="Global Airlines",
            conversion_rate=1.5,
            min_points=1000
        )
    ]

@router.post("/promotions/apply-to-transaction", response_model=List[PointsBonus])
async def apply_promotions(request: TransactionRequest):
    """
    Apply relevant promotions to a transaction to calculate bonus points.
    """
    # Using model_dump() for Pydantic v2 compatibility
    transaction_dict = request.model_dump()
    return await campaign_service.apply_promotions(request.member_id, transaction_dict)

@router.get("/members/{id}/personalized-offers", response_model=List[RewardSchema])
async def get_personalized_offers(id: int):
    """
    Get personalized reward offers for a member.
    """
    offers = await campaign_service.generate_targeted_offers(id)
    # Since the service returns SQLAlchemy models (or mocks mimicking them),
    # we rely on from_attributes=True in RewardSchema to serialize them.
    # If the service returns an empty list, that works too.
    return offers
