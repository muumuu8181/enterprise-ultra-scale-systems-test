import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.models.base import Base
from src.models.carbon_models import EmissionSource, CarbonCredit, EmissionSourceType, EmissionScope, CreditStatus
from src.services.carbon_service import CarbonService

# Use in-memory SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_calculate_carbon_footprint(db_session):
    # Setup
    emission1 = EmissionSource(
        entity_id="company_a",
        source_type=EmissionSourceType.INDUSTRIAL,
        scope=EmissionScope.SCOPE_1,
        reported_co2_kt=100.5
    )
    emission2 = EmissionSource(
        entity_id="company_a",
        source_type=EmissionSourceType.TRANSPORT,
        scope=EmissionScope.SCOPE_2,
        reported_co2_kt=50.0
    )
    db_session.add(emission1)
    db_session.add(emission2)
    await db_session.commit()

    # Test Service
    service = CarbonService()
    footprint = await service.calculate_carbon_footprint(db_session, "company_a", 2023)

    assert footprint == 150.5

@pytest.mark.asyncio
async def test_optimize_offset_portfolio(db_session):
    # Setup
    # Price is $10/ton in mock logic
    # Budget $1200 -> can buy 120 tons.

    # Large credit: 100 tons ($1000)
    credit1 = CarbonCredit(
        project_id="p1",
        vintage_year=2020,
        volume_tco2=100.0,
        status=CreditStatus.ISSUED,
        registry="Verra"
    )
    # Medium credit: 50 tons ($500)
    credit2 = CarbonCredit(
        project_id="p2",
        vintage_year=2021,
        volume_tco2=50.0,
        status=CreditStatus.ISSUED,
        registry="Gold Standard"
    )

    db_session.add(credit1)
    db_session.add(credit2)
    await db_session.commit()

    service = CarbonService()
    # Budget $1200. Max volume 120.
    # Sorted by volume desc: p1(100), p2(50).
    # Try p1: 100 <= 120. Add p1. Current 100.
    # Try p2: 100 + 50 = 150 > 120. Skip p2.
    # Result: [p1]

    portfolio = await service.optimize_offset_portfolio(db_session, 1200.0)

    assert len(portfolio) == 1
    assert portfolio[0].project_id == "p1"

    # Test with enough budget
    portfolio_all = await service.optimize_offset_portfolio(db_session, 2000.0)
    assert len(portfolio_all) == 2

@pytest.mark.asyncio
async def test_generate_netzero_pathway(db_session):
    service = CarbonService()
    roadmap = await service.generate_netzero_pathway(db_session, "company_b")

    assert roadmap["entity_id"] == "company_b"
    assert "steps" in roadmap
    assert len(roadmap["steps"]) > 0
