import pytest
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone, timedelta

# Add src to pythonpath
sys.path.append(os.getcwd())

from src.models.subscription_models import Base, Plan, Subscription, PlanInterval, SubscriptionStatus
from src.services.billing_service import BillingService

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    # Use StaticPool to persist memory db across sessions in same thread
    engine = create_async_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_billing_service_flow(db_session):
    # 1. Create a Plan
    plan = Plan(
        name="Pro Plan",
        interval=PlanInterval.MONTHLY,
        price=29.99,
        trial_days=14,
        features={"unlimited": True},
        usage_limits={"api_calls": 1000}
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    # 2. Create a Subscription
    sub = Subscription(
        customer_id="cust_123",
        plan_id=plan.id,
        status=SubscriptionStatus.TRIALING,
        current_period_end=datetime.now(timezone.utc)
    )
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(sub)

    # 3. Use BillingService
    service = BillingService(db_session)

    # Test handle_trial_end
    # Currently status is TRIALING. calling handle_trial_end should make it ACTIVE
    await service.handle_trial_end(sub.id)
    # Need to refresh sub to see changes
    await db_session.refresh(sub)

    assert sub.status == SubscriptionStatus.ACTIVE
    # Should be extended by 30 days
    # Check if period end is roughly 30 days from now

    # Handle timezone issues with SQLite (it might return naive datetime)
    current_end = sub.current_period_end
    if current_end.tzinfo is None:
        current_end = current_end.replace(tzinfo=timezone.utc)

    assert current_end > datetime.now(timezone.utc) + timedelta(days=29)

    # Test generate_invoice
    invoice = await service.generate_invoice(sub.id)
    assert invoice.amount_due == 29.99
    assert invoice.status == "draft"

    # Test apply_proration
    # Create new plan
    new_plan = Plan(
        name="Enterprise Plan",
        interval=PlanInterval.ANNUAL,
        price=299.99,
        trial_days=0,
        features={},
        usage_limits={}
    )
    db_session.add(new_plan)
    await db_session.commit()
    await db_session.refresh(new_plan)

    proration = await service.apply_proration(sub.id, new_plan.id)

    assert proration.old_plan_id == plan.id
    assert proration.new_plan_id == new_plan.id

    # Check if subscription plan_id is updated
    await db_session.refresh(sub)
    assert sub.plan_id == new_plan.id

    # Mocked values in service
    assert proration.prorated_amount == 100.0
    assert proration.credit_applied == 20.0
    assert proration.amount_due == 80.0
