import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from datetime import date
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.ground_ops import Base, GroundCrew, Turnaround, BaggageCarousel, CrewType, TurnaroundStatus, CarouselStatus
from src.services.turnaround_service import optimize_crew_deployment

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with AsyncSessionLocal() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_ground_crew_model(db_session):
    crew = GroundCrew(
        crew_type=CrewType.baggage,
        shift="morning",
        assigned_flight_id="JL123"
    )
    db_session.add(crew)
    await db_session.commit()

    result = await db_session.execute(select(GroundCrew).where(GroundCrew.assigned_flight_id == "JL123"))
    saved_crew = result.scalar_one()
    assert saved_crew.crew_type == CrewType.baggage
    assert saved_crew.shift == "morning"

@pytest.mark.asyncio
async def test_turnaround_model(db_session):
    turnaround = Turnaround(
        flight_id="JL123",
        target_minutes=45,
        status=TurnaroundStatus.pending
    )
    db_session.add(turnaround)
    await db_session.commit()

    result = await db_session.execute(select(Turnaround).where(Turnaround.flight_id == "JL123"))
    saved = result.scalar_one()
    assert saved.target_minutes == 45
    assert saved.status == TurnaroundStatus.pending

@pytest.mark.asyncio
async def test_baggage_carousel_model(db_session):
    carousel = BaggageCarousel(
        terminal="T1",
        carousel_number=1,
        status=CarouselStatus.idle
    )
    db_session.add(carousel)
    await db_session.commit()

    result = await db_session.execute(select(BaggageCarousel).where(BaggageCarousel.terminal == "T1"))
    saved = result.scalar_one()
    assert saved.carousel_number == 1
    assert saved.status == CarouselStatus.idle

@pytest.mark.asyncio
async def test_optimize_crew_deployment():
    # Unit test for service function
    schedule = await optimize_crew_deployment(date.today())
    assert schedule.date == date.today()
    assert len(schedule.assignments) > 0
