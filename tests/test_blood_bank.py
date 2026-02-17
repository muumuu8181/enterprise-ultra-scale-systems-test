import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from src.main import app
from src.database import get_db, Base
from src.models.blood_bank_models import BloodType, BloodComponent, BloodUnitStatus, UrgencyLevel

# Setup test DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

@pytest_asyncio.fixture
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_create_donor(client, test_db):
    response = await client.post("/api/v1/blood-bank/donors", json={
        "name": "John Doe",
        "blood_type": "A_pos",
        "eligible": True,
        "contact_info": {"email": "john@example.com"}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["id"] is not None
    return data["id"]

@pytest.mark.asyncio
async def test_register_donation(client, test_db):
    # Create donor first
    donor_res = await client.post("/api/v1/blood-bank/donors", json={
        "name": "Jane Doe",
        "blood_type": "O_neg",
        "eligible": True
    })
    donor_id = donor_res.json()["id"]

    response = await client.post("/api/v1/blood-bank/donations/register", json={
        "donor_id": donor_id,
        "blood_type": "O_neg",
        "component": "whole_blood",
        "collection_date": "2023-10-27",
        "expiry_date": "2023-12-01",
        "volume_ml": 450,
        "storage_location": "Fridge A"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["donor_id"] == donor_id
    assert data["status"] == "collected"

@pytest.mark.asyncio
async def test_inventory(client, test_db):
    # Register a donation
    donor_res = await client.post("/api/v1/blood-bank/donors", json={"name": "Bob", "blood_type": "B_pos"})
    donor_id = donor_res.json()["id"]

    await client.post("/api/v1/blood-bank/donations/register", json={
        "donor_id": donor_id,
        "blood_type": "B_pos",
        "component": "platelets",
        "collection_date": "2023-10-27",
        "expiry_date": "2023-11-01",
        "volume_ml": 200,
        "storage_location": "Shelf 1",
        "status": "available"
    })

    response = await client.get("/api/v1/blood-bank/inventory?blood_type=B_pos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["blood_type"] == "B_pos"

@pytest.mark.asyncio
async def test_create_request(client, test_db):
    response = await client.post("/api/v1/blood-bank/requests/create", json={
        "patient_id": "P001",
        "hospital_id": "H001",
        "blood_type": "A_pos",
        "component": "rbc",
        "units_needed": 2,
        "urgency": "urgent"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "requested"

@pytest.mark.asyncio
async def test_crossmatch(client, test_db):
    response = await client.get("/api/v1/blood-bank/compatibility/crossmatch?donor=O_neg&patient=A_pos&component=rbc")
    assert response.status_code == 200
    assert response.json() is True

    response = await client.get("/api/v1/blood-bank/compatibility/crossmatch?donor=A_pos&patient=B_pos&component=rbc")
    assert response.status_code == 200
    assert response.json() is False
