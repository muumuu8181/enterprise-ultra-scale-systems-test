from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.auction_finance import EscrowAccount, EscrowStatus

class PaymentResult(BaseModel):
    success: bool
    transaction_id: str
    message: str

class ReleaseResult(BaseModel):
    success: bool
    status: str
    message: str

async def calculate_buyers_premium(lot_id: str, hammer_price: float, db: AsyncSession = None) -> float:
    # Logic to calculate buyer's premium based on tiers
    # Placeholder implementation: 15% flat rate
    return hammer_price * 0.15

async def process_payment(lot_id: str, buyer_id: str, method: str) -> PaymentResult:
    # Logic to process payment via Stripe (mock)
    # Return success
    return PaymentResult(success=True, transaction_id=f"pay_{lot_id}_{buyer_id}", message="Payment processed successfully")

async def release_escrow(escrow_id: int, db: AsyncSession) -> ReleaseResult:
    # Logic to release escrow
    if not db:
        raise ValueError("Database session is required")

    result = await db.execute(select(EscrowAccount).where(EscrowAccount.id == escrow_id))
    escrow = result.scalars().first()

    if not escrow:
        return ReleaseResult(success=False, status="not_found", message="Escrow account not found")

    escrow.status = EscrowStatus.RELEASED
    await db.commit()
    await db.refresh(escrow)

    return ReleaseResult(success=True, status=escrow.status.value, message="Escrow released successfully")
