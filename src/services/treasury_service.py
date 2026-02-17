from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Dict, Any
from src.models.treasury_models import TreasuryAsset, GrantApplication, MultisigTransaction, AssetType, TransactionType
import datetime

class PaymentResult(BaseModel):
    success: bool
    transaction_id: str
    message: str

async def calculate_runway(dao_id: str, db: AsyncSession) -> Dict[str, Any]:
    # Fetch all stablecoin assets
    stmt = select(TreasuryAsset).where(
        TreasuryAsset.dao_id == dao_id,
        TreasuryAsset.asset_type == AssetType.STABLECOIN
    )
    result = await db.execute(stmt)
    assets = result.scalars().all()

    total_stable_usd = sum(asset.usd_value for asset in assets)

    # Mock burn rate (e.g., $10,000/month)
    # In a real system, this would be calculated from historical expenses
    monthly_burn_rate = 10000.0

    runway_months = total_stable_usd / monthly_burn_rate if monthly_burn_rate > 0 else 0

    return {
        "dao_id": dao_id,
        "total_stable_usd": total_stable_usd,
        "monthly_burn_rate": monthly_burn_rate,
        "runway_months": runway_months
    }

async def auto_diversify_treasury(dao_id: str, allocation: Dict[str, float], db: AsyncSession):
    # allocation example: {"token": 0.5, "stablecoin": 0.5}

    # Fetch all assets
    stmt = select(TreasuryAsset).where(TreasuryAsset.dao_id == dao_id)
    result = await db.execute(stmt)
    assets = result.scalars().all()

    total_value = sum(asset.usd_value for asset in assets)
    if total_value == 0:
        return {"message": "Treasury is empty"}

    current_allocation = {}
    for asset in assets:
        asset_type_str = asset.asset_type.value
        current_allocation[asset_type_str] = current_allocation.get(asset_type_str, 0) + asset.usd_value

    # Calculate difference and propose swaps
    swaps_proposed = []

    # Logic to balance (simplified: just check stablecoin target)
    target_stable_ratio = allocation.get("stablecoin", 0.0)
    current_stable_value = current_allocation.get("stablecoin", 0.0)
    target_stable_value = total_value * target_stable_ratio

    if current_stable_value < target_stable_value:
        diff = target_stable_value - current_stable_value
        # Propose swap from TOKEN to STABLECOIN
        # Find a token asset to sell
        token_asset = next((a for a in assets if a.asset_type == AssetType.TOKEN), None)
        if token_asset:
            tx = MultisigTransaction(
                dao_id=dao_id,
                tx_type=TransactionType.SWAP,
                amount=diff, # USD value to swap
                recipient="DEX_ROUTER",
                signers_required=2,
                signatures=[],
                executed=False
            )
            db.add(tx)
            swaps_proposed.append(f"Swap {diff} USD of {token_asset.token_address} to Stablecoin")

    await db.commit()

    return {"message": "Diversification checked", "proposals": swaps_proposed}

async def process_grant_milestone(grant_id: int, milestone_id: int, db: AsyncSession) -> PaymentResult:
    stmt = select(GrantApplication).where(GrantApplication.id == grant_id)
    result = await db.execute(stmt)
    grant = result.scalar_one_or_none()

    if not grant:
        return PaymentResult(success=False, transaction_id="", message="Grant not found")

    # Check milestone
    milestones = grant.milestones or []
    milestone_found = False
    amount_to_pay = 0.0

    updated_milestones = []
    for m in milestones:
        if m.get("id") == milestone_id:
            if m.get("status") == "completed":
                 return PaymentResult(success=False, transaction_id="", message="Milestone already completed")
            m["status"] = "completed"
            amount_to_pay = m.get("amount", 0.0)
            milestone_found = True
        updated_milestones.append(m)

    if not milestone_found:
        return PaymentResult(success=False, transaction_id="", message="Milestone not found")

    # Create payment transaction
    tx = MultisigTransaction(
        dao_id=grant.dao_id,
        tx_type=TransactionType.PAYMENT,
        amount=amount_to_pay,
        recipient=grant.applicant_address,
        signers_required=2,
        signatures=[],
        executed=False
    )
    db.add(tx)

    # Update grant milestones
    # Note: SQLAlchemy might not track mutation of JSON field automatically if we don't reassign
    grant.milestones = list(updated_milestones)

    await db.commit()
    await db.refresh(tx)

    return PaymentResult(success=True, transaction_id=str(tx.id), message="Payment transaction created")
