import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
from sqlalchemy import String

from src.main import app
from src.core.database import Base, get_db
from src.models.rental_models import Vehicle, VehicleCategory, VehicleStatus, RentalBooking, BookingStatus, Insurance, InsuranceType

# Patch models to use String instead of Geometry for SQLite tests
# This must be done before create_all
Vehicle.__table__.c.location.type = String()
RentalBooking.__table__.c.pickup_location.type = String()

# Also need to ensure the TypeEngine doesn't trigger GeoAlchemy2 compilation
# Since we replaced the type instance in the table, it should be fine.

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
# Set expire_on_commit=False to avoid MissingGreenlet
TestingSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture(scope="function")
async def db_session():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_and_get_vehicle(client, db_session):
    vehicle = Vehicle(
        make="Toyota",
        model="Camry",
        year=2022,
        license_plate="TEST-123",
        category=VehicleCategory.ECONOMY,
        daily_rate=50.0,
        status=VehicleStatus.AVAILABLE,
    )
    db_session.add(vehicle)
    await db_session.commit()
    # No refresh needed due to expire_on_commit=False, object is still valid but might not have defaults if DB generated them.
    # But id is generated. We should refresh to get ID.
    await db_session.refresh(vehicle)

    response = await client.get("/api/v1/vehicles/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["make"] == "Toyota"
    assert data[0]["id"] == vehicle.id

@pytest.mark.asyncio
async def test_book_vehicle(client, db_session):
    vehicle = Vehicle(
        make="Honda",
        model="Civic",
        year=2023,
        license_plate="TEST-456",
        category=VehicleCategory.ECONOMY,
        daily_rate=60.0,
        status=VehicleStatus.AVAILABLE
    )
    db_session.add(vehicle)
    await db_session.commit()
    await db_session.refresh(vehicle)

    booking_data = {
        "pickup_date": "2023-10-01T10:00:00",
        "return_date": "2023-10-05T10:00:00",
        "insurance_type": "basic",
        "renter_id": 1
    }

    response = await client.post(f"/api/v1/vehicles/{vehicle.id}/book", json=booking_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["total_price"] > 0

@pytest.mark.asyncio
async def test_availability(client, db_session):
    vehicle = Vehicle(
        make="Ford",
        model="Focus",
        year=2021,
        license_plate="TEST-789",
        category=VehicleCategory.ECONOMY,
        daily_rate=40.0,
        status=VehicleStatus.AVAILABLE
    )
    db_session.add(vehicle)
    await db_session.commit()
    await db_session.refresh(vehicle)

    booking = RentalBooking(
        vehicle_id=vehicle.id,
        renter_id=1,
        pickup_date=datetime(2023, 11, 10),
        return_date=datetime(2023, 11, 15),
        total_price=200.0,
        status=BookingStatus.CONFIRMED
    )
    db_session.add(booking)
    await db_session.commit()

    # Pass datetime as string parameters in query? No, datetime objects in model, string in query
    response = await client.get(f"/api/v1/vehicles/{vehicle.id}/availability?month=2023-11")
    assert response.status_code == 200
    data = response.json()
    available_days = data["available_days"]

    booked_dates = ["2023-11-10", "2023-11-11", "2023-11-12", "2023-11-13", "2023-11-14"]
    for d in available_days:
        assert d not in booked_dates
