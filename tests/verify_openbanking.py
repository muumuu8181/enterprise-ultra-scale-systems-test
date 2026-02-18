import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.main import app
from src.core.database import get_db, Base
from src.models.openbanking_models import Consent  # Import to ensure models are registered

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def override_get_db() -> AsyncGenerator:
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def run_tests():
    # Run async setup
    asyncio.run(init_db())

    client = TestClient(app)

    print("\n--- Starting Verification ---")

    # 1. Create Consent
    print("1. Creating Consent...")
    response = client.post(
        "/openbanking/consents",
        json={
            "client_id": "client_123",
            "customer_id": "cust_456",
            "scopes": {"accounts": "read", "transactions": "read"},
            "redirect_uri": "http://example.com/callback"
        }
    )
    if response.status_code != 201:
        print(f"Failed to create consent: {response.text}")
        exit(1)

    data = response.json()
    consent_id = data["id"]
    print(f"   Success: Consent ID {consent_id} created with status {data['status']}")

    # 2. Get Accounts
    print("2. Getting Accounts...")
    response = client.get(f"/openbanking/accounts/{consent_id}")
    if response.status_code != 200:
        print(f"Failed to get accounts: {response.text}")
        exit(1)
    accounts = response.json()
    print(f"   Success: Retrieved {len(accounts)} accounts")

    # 3. Get Transactions
    print("3. Getting Transactions...")
    response = client.get(f"/openbanking/transactions/{consent_id}")
    if response.status_code != 200:
        print(f"Failed to get transactions: {response.text}")
        exit(1)
    txs = response.json()
    print(f"   Success: Retrieved {len(txs)} transactions")

    # 4. Revoke Consent
    print("4. Revoking Consent...")
    response = client.delete(f"/openbanking/consents/{consent_id}")
    if response.status_code != 204:
        print(f"Failed to revoke consent: {response.text}")
        exit(1)
    print("   Success: Consent revoked")

    # 5. Verify Revocation
    print("5. Verifying Access Denied...")
    response = client.get(f"/openbanking/accounts/{consent_id}")
    if response.status_code == 401:
        print("   Success: Access denied (401) as expected")
    else:
        print(f"Failed: Expected 401 but got {response.status_code}")
        exit(1)

    print("\n--- Verification Passed! ---")

if __name__ == "__main__":
    run_tests()
