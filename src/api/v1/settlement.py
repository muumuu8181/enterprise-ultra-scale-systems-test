from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from src.database import get_db
from src.services.settlement_service import (
    calculate_buyers_premium,
    process_payment,
    release_escrow,
    PaymentResult,
    ReleaseResult
)
from src.models.auction_finance import AuctionSettlement, EscrowAccount

router = APIRouter()

class PaymentRequest(BaseModel):
    buyer_id: str
    method: str

class COARequest(BaseModel):
    verification_code: str
    issued_by: str

@router.post("/lots/{lot_id}/payment", response_model=PaymentResult)
async def make_payment(lot_id: str, request: PaymentRequest, db: AsyncSession = Depends(get_db)):
    # Mock hammer price fetching
    hammer_price = 1000.0

    # Process payment
    payment_result = await process_payment(lot_id, request.buyer_id, request.method)

    if payment_result.success:
        # Create settlement record
        premium = await calculate_buyers_premium(lot_id, hammer_price, db)

        # Check if exists to avoid unique constraint error, or just create new one
        result = await db.execute(select(AuctionSettlement).where(AuctionSettlement.lot_id == lot_id))
        existing = result.scalars().first()

        if not existing:
            settlement = AuctionSettlement(
                lot_id=lot_id,
                hammer_price=hammer_price,
                buyers_premium=premium,
                seller_proceeds=hammer_price,
                platform_commission=premium
            )
            db.add(settlement)
            await db.commit()

    return payment_result

@router.get("/lots/{lot_id}/settlement-details")
async def get_settlement_details(lot_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuctionSettlement).where(AuctionSettlement.lot_id == lot_id))
    settlement = result.scalars().first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    return settlement

@router.get("/sellers/{seller_id}/proceeds-report")
async def get_proceeds_report(seller_id: str, db: AsyncSession = Depends(get_db)):
    # In a real scenario, this would aggregate AuctionSettlement data for the seller
    return {
        "seller_id": seller_id,
        "total_proceeds": 5000.0,
        "currency": "USD",
        "period": "2023-Q4"
    }

@router.post("/escrow/{escrow_id}/release", response_model=ReleaseResult)
async def release_escrow_endpoint(escrow_id: int, db: AsyncSession = Depends(get_db)):
    result = await release_escrow(escrow_id, db)
    if not result.success:
        status_code = 404 if result.status == "not_found" else 400
        raise HTTPException(status_code=status_code, detail=result.message)
    return result

@router.post("/lots/{lot_id}/certificate-of-authenticity")
async def generate_coa(lot_id: str, request: COARequest):
    return {
        "message": "Certificate generated successfully",
        "lot_id": lot_id,
        "certificate_id": f"cert_{lot_id}_{request.verification_code}",
        "issued_by": request.issued_by
    }
