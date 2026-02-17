import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.core.database import get_db
from src.models.base import Base
from src.models.account_models import Account
from src.models.card_models import Card

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine):
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture(scope="function")
async def client(test_session):
    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    # Use ASGITransport to avoid real network calls
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_account_and_issue_card(client, test_session):
    # Create account
    account = Account(name="Test User", email="test@example.com")
    test_session.add(account)
    await test_session.commit()
    await test_session.refresh(account)

    response = await client.post("/cards/issue", json={"account_id": account.id, "card_type": "debit"})
    assert response.status_code == 201
    data = response.json()
    assert data["account_id"] == account.id
    assert "pan" in data
    assert "cvv" in data
    assert data["status"] == "active"

@pytest.mark.asyncio
async def test_get_card(client, test_session):
    account = Account(name="Test User 2", email="test2@example.com")
    test_session.add(account)
    await test_session.commit()
    await test_session.refresh(account)

    issue_res = await client.post("/cards/issue", json={"account_id": account.id, "card_type": "credit"})
    card_id = issue_res.json()["id"]

    response = await client.get(f"/cards/{card_id}")
    assert response.status_code == 200
    assert response.json()["id"] == card_id

@pytest.mark.asyncio
async def test_freeze_unfreeze(client, test_session):
    account = Account(name="Test User 3", email="test3@example.com")
    test_session.add(account)
    await test_session.commit()

    issue_res = await client.post("/cards/issue", json={"account_id": account.id, "card_type": "debit"})
    card_id = issue_res.json()["id"]

    # Freeze
    res = await client.post(f"/cards/{card_id}/freeze")
    assert res.status_code == 200
    assert res.json()["status"] == "frozen"

    # Unfreeze
    res = await client.post(f"/cards/{card_id}/unfreeze")
    assert res.status_code == 200
    assert res.json()["status"] == "active"

@pytest.mark.asyncio
async def test_update_limits(client, test_session):
    account = Account(name="Test User 4", email="test4@example.com")
    test_session.add(account)
    await test_session.commit()

    issue_res = await client.post("/cards/issue", json={"account_id": account.id, "card_type": "debit"})
    card_id = issue_res.json()["id"]

    res = await client.put(f"/cards/{card_id}/limits", json={"daily_limit": 100.0})
    assert res.status_code == 200
    assert res.json()["daily_limit"] == 100.0

@pytest.mark.asyncio
async def test_issue_virtual_card(client, test_session):
    account = Account(name="Test User 5", email="test5@example.com")
    test_session.add(account)
    await test_session.commit()

    # Original card
    issue_res = await client.post("/cards/issue", json={"account_id": account.id, "card_type": "debit"})
    card_id = issue_res.json()["id"]

    # Virtual card
    res = await client.post(f"/cards/{card_id}/virtual")
    assert res.status_code == 201
    data = res.json()
    assert data["account_id"] == account.id
    assert data["id"] != card_id
    assert "pan" in data

from src.services.card_service import CardService

@pytest.mark.asyncio
async def test_service_payment_limits(test_session):
    # Setup
    account = Account(name="Test User 6", email="test6@example.com")
    test_session.add(account)
    await test_session.commit()

    service = CardService(test_session)
    card, _, _ = await service.issue_card(account.id, "debit")
    await service.update_limits(card.id, daily_limit=1000.0)

    # 1st payment: 600 -> OK
    await service.process_payment(card.id, 600.0, "Merchant A")

    # 2nd payment: 300 -> OK (Total 900)
    await service.process_payment(card.id, 300.0, "Merchant B")

    # 3rd payment: 200 -> Fail (Total 1100 > 1000)
    with pytest.raises(Exception) as excinfo:
        await service.process_payment(card.id, 200.0, "Merchant C")
    assert "Exceeds limit" in str(excinfo.value)
