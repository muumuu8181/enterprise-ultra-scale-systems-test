import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from src.main import app
from src.database import Base, get_db
from src.models.pharmacy_models import Medication, Dispensing

# Setup in-memory DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

@pytest.fixture(scope="function")
async def db_session():
    # Only create/drop relevant tables to avoid GeoAlchemy2 dependency issues with SQLite
    tables = [Medication.__table__, Dispensing.__table__]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all, tables=tables)

@pytest.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_search_medications(client, db_session):
    # Seed
    med1 = Medication(name="Aspirin", generic_name="Acetylsalicylic acid", category="Painkiller", dosage_form="Tablet", stock_quantity=100)
    med2 = Medication(name="Amoxicillin", generic_name="Amoxicillin", category="Antibiotic", dosage_form="Capsule", stock_quantity=50)
    db_session.add_all([med1, med2])
    await db_session.commit()

    response = await client.get("/api/v1/pharmacy/medications")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Search
    response = await client.get("/api/v1/pharmacy/medications?search=Asp")
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Aspirin"

@pytest.mark.asyncio
async def test_dispense_medication(client, db_session):
    med = Medication(name="Xanax", generic_name="Alprazolam", category="Anxiety", dosage_form="Tablet", stock_quantity=10)
    db_session.add(med)
    await db_session.commit()
    await db_session.refresh(med)

    payload = {
        "medication_id": med.id,
        "pharmacist_id": 1,
        "quantity": 5,
        "batch_number": "BATCH123"
    }
    response = await client.post("/api/v1/pharmacy/prescriptions/999/dispense", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 5

    # Check stock update
    await db_session.refresh(med)
    assert med.stock_quantity == 5

@pytest.mark.asyncio
async def test_dispense_insufficient_stock(client, db_session):
    med = Medication(name="LowStock", generic_name="Low", category="Test", dosage_form="Tab", stock_quantity=2)
    db_session.add(med)
    await db_session.commit()
    await db_session.refresh(med)

    payload = {
        "medication_id": med.id,
        "pharmacist_id": 1,
        "quantity": 5,
        "batch_number": "BATCH123"
    }
    response = await client.post("/api/v1/pharmacy/prescriptions/999/dispense", json=payload)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_reorder_inventory(client, db_session):
    med = Medication(name="ReorderMe", generic_name="Re", category="Test", dosage_form="Tab", stock_quantity=10)
    db_session.add(med)
    await db_session.commit()
    await db_session.refresh(med)

    payload = {
        "medication_id": med.id,
        "quantity": 50
    }
    response = await client.post("/api/v1/pharmacy/inventory/reorder", json=payload)
    assert response.status_code == 200

    await db_session.refresh(med)
    assert med.stock_quantity == 60

@pytest.mark.asyncio
async def test_pending_prescriptions(client):
    response = await client.get("/api/v1/pharmacy/prescriptions/pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 0
