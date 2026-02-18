import pytest
from httpx import AsyncClient
import uuid
from src.models.customer import Customer
from decimal import Decimal

@pytest.mark.asyncio
async def test_create_account_flow(client: AsyncClient, db_session):
    # Create a customer directly in DB
    customer_id = uuid.uuid4()
    customer = Customer(customer_id=customer_id, name="Test Customer", tax_id="12345")
    db_session.add(customer)
    await db_session.commit()

    # Test Create Account
    response = await client.post("/api/v1/accounts/", json={
        "customer_id": str(customer_id),
        "account_type": "SAVINGS",
        "currency": "JPY"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["customer_id"] == str(customer_id)
    account_id = data["account_id"]

    # Test Get Account
    response = await client.get(f"/api/v1/accounts/{account_id}")
    assert response.status_code == 200
    assert response.json()["account_id"] == account_id

    # Test Get Non-existent Account
    response = await client.get(f"/api/v1/accounts/{uuid.uuid4()}")
    assert response.status_code == 404
