from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from datetime import date

from src.core.database import SessionLocal
from src.models.monetization import RevenueSplit, ProviderPayout, APIReview
from src.services.analytics_service import compute_api_health_score, generate_provider_report, ProviderReport
from pydantic import BaseModel

router = APIRouter()

# Dependency
async def get_db():
    async with SessionLocal() as session:
        yield session

# Pydantic models for request/response
class PayoutRequest(BaseModel):
    amount: float
    currency: str = "USD"

class ReviewCreate(BaseModel):
    reviewer_id: str
    rating: int
    review_text: str

class ReviewResponse(BaseModel):
    id: int
    product_id: str
    reviewer_id: str
    rating: int
    review_text: str
    helpful_count: int
    verified_subscriber: bool

    class Config:
        from_attributes = True

class TrendingAPI(BaseModel):
    product_id: str
    popularity_score: float
    health_score: float

@router.get("/providers/{provider_id}/earnings-dashboard")
async def get_earnings_dashboard(provider_id: str, period: Optional[date] = None):
    if not period:
        period = date.today().replace(day=1)

    report = await generate_provider_report(provider_id, period)
    return report

@router.get("/providers/{provider_id}/payouts")
async def get_payouts(provider_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProviderPayout).filter(ProviderPayout.provider_id == provider_id))
    payouts = result.scalars().all()
    return payouts

@router.post("/providers/{provider_id}/payout-request")
async def request_payout(provider_id: str, request: PayoutRequest, db: AsyncSession = Depends(get_db)):
    # Logic to process payout request
    # Validate balance, create transaction, etc.
    return {"status": "processing", "amount": request.amount, "provider_id": provider_id}

@router.get("/products/{product_id}/reviews", response_model=List[ReviewResponse])
async def get_reviews(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIReview).filter(APIReview.product_id == product_id))
    reviews = result.scalars().all()
    return reviews

@router.post("/products/{product_id}/reviews", response_model=ReviewResponse)
async def create_review(product_id: str, review: ReviewCreate, db: AsyncSession = Depends(get_db)):
    new_review = APIReview(
        product_id=product_id,
        reviewer_id=review.reviewer_id,
        rating=review.rating,
        review_text=review.review_text,
        helpful_count=0,
        verified_subscriber=False # Default for now
    )
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review

@router.get("/analytics/trending-apis", response_model=List[TrendingAPI])
async def get_trending_apis():
    # Mock data for trending APIs
    return [
        TrendingAPI(product_id="prod_123", popularity_score=98.5, health_score=await compute_api_health_score("prod_123")),
        TrendingAPI(product_id="prod_456", popularity_score=92.0, health_score=await compute_api_health_score("prod_456")),
    ]
