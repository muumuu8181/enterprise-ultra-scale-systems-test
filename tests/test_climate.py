import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.db.base import Base
from src.models.climate_models import WeatherStation, ClimateReading, ClimateModel, ModelType
from src.services.climate_service import ClimateService
from datetime import datetime

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_create_weather_station(db_session):
    station = WeatherStation(
        station_id="ST_TEST",
        latitude=10.0,
        longitude=20.0,
        elevation=100.0,
        status="active",
        last_reading_at=datetime.utcnow()
    )
    db_session.add(station)
    await db_session.commit()

    assert station.id is not None
    assert station.station_id == "ST_TEST"

@pytest.mark.asyncio
async def test_climate_service_interpolate(db_session):
    # Setup data
    station = WeatherStation(
        station_id="ST_1",
        latitude=10.0,
        longitude=20.0,
        elevation=100.0
    )
    db_session.add(station)

    reading = ClimateReading(
        station_id="ST_1",
        timestamp=datetime.utcnow(),
        temperature=25.0,
        humidity=50.0
    )
    db_session.add(reading)
    await db_session.commit()

    service = ClimateService(db_session)
    result = await service.interpolate_spatial(10.0, 20.0, "temperature")
    assert result == 25.0

@pytest.mark.asyncio
async def test_climate_service_extreme_events(db_session):
    service = ClimateService(db_session)
    events = await service.detect_extreme_events((0,0,10,10), 30.0)
    assert len(events) == 1
    assert events[0].event_type == "Heatwave"

@pytest.mark.asyncio
async def test_climate_service_interpolate_invalid_variable(db_session):
    service = ClimateService(db_session)
    with pytest.raises(ValueError):
        await service.interpolate_spatial(10.0, 20.0, "invalid_variable")
