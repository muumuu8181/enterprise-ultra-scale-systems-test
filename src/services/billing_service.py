from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, timedelta
from src.models.subscription_models import Subscription, Plan, Invoice, ProrationResult, SubscriptionStatus, PlanInterval

class BillingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle_trial_end(self, subscription_id: int):
        stmt = select(Subscription).options(selectinload(Subscription.plan)).where(Subscription.id == subscription_id)
        result = await self.db.execute(stmt)
        sub = result.scalar_one_or_none()

        if not sub:
            raise ValueError(f"Subscription {subscription_id} not found")

        if sub.status == SubscriptionStatus.TRIALING:
            # Logic to activate
            sub.status = SubscriptionStatus.ACTIVE
            now = datetime.now(timezone.utc)

            if sub.plan.interval == PlanInterval.MONTHLY:
                sub.current_period_end = now + timedelta(days=30)
            elif sub.plan.interval == PlanInterval.QUARTERLY:
                sub.current_period_end = now + timedelta(days=90)
            elif sub.plan.interval == PlanInterval.ANNUAL:
                sub.current_period_end = now + timedelta(days=365)

            await self.db.commit()
            await self.db.refresh(sub)

    async def generate_invoice(self, subscription_id: int) -> Invoice:
        stmt = select(Subscription).options(selectinload(Subscription.plan)).where(Subscription.id == subscription_id)
        result = await self.db.execute(stmt)
        sub = result.scalar_one_or_none()

        if not sub:
            raise ValueError(f"Subscription {subscription_id} not found")

        amount = sub.plan.price
        # logic for usage could be added here

        return Invoice(
            id=f"inv_{subscription_id}_{int(datetime.now(timezone.utc).timestamp())}",
            subscription_id=subscription_id,
            amount_due=amount,
            currency="USD",
            status="draft",
            period_start=datetime.now(timezone.utc),
            period_end=sub.current_period_end
        )

    async def apply_proration(self, subscription_id: int, new_plan_id: int) -> ProrationResult:
        stmt = select(Subscription).options(selectinload(Subscription.plan)).where(Subscription.id == subscription_id)
        result = await self.db.execute(stmt)
        sub = result.scalar_one_or_none()

        if not sub:
            raise ValueError(f"Subscription {subscription_id} not found")

        old_plan_id = sub.plan.id

        # Update subscription to new plan
        sub.plan_id = new_plan_id

        await self.db.commit()
        await self.db.refresh(sub)

        # In a real app, calculate unused time on old plan vs time on new plan
        # Mock implementation

        return ProrationResult(
            old_plan_id=old_plan_id,
            new_plan_id=new_plan_id,
            prorated_amount=100.0, # Mock
            credit_applied=20.0,   # Mock
            amount_due=80.0        # Mock
        )
