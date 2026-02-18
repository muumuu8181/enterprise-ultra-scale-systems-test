import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_make_payment(client: AsyncClient):
    # Make a payment
    response = await client.post("/api/v1/lots/lot123/payment", json={"buyer_id": "buyer456", "method": "card"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == True
    assert "transaction_id" in data

    # Check if settlement was created
    response = await client.get("/api/v1/lots/lot123/settlement-details")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["lot_id"] == "lot123"
    assert data["hammer_price"] == 1000.0

@pytest.mark.asyncio
async def test_get_proceeds_report(client: AsyncClient):
    response = await client.get("/api/v1/sellers/seller789/proceeds-report")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["seller_id"] == "seller789"

@pytest.mark.asyncio
async def test_release_escrow(client: AsyncClient, db):
    # Seed data
    from src.models.auction_finance import EscrowAccount, EscrowStatus
    escrow = EscrowAccount(lot_id="lot999", buyer_id="buyer888", amount=500.0, status=EscrowStatus.HELD)
    db.add(escrow)
    await db.commit()
    await db.refresh(escrow)

    # Release escrow
    response = await client.post(f"/api/v1/escrow/{escrow.id}/release")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == True
    assert data["status"] == "released"

    # Verify DB update
    await db.refresh(escrow)
    assert escrow.status == EscrowStatus.RELEASED

@pytest.mark.asyncio
async def test_generate_coa(client: AsyncClient):
    response = await client.post("/api/v1/lots/lot555/certificate-of-authenticity", json={"verification_code": "AUTH123", "issued_by": "ExpertA"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["lot_id"] == "lot555"
    assert "certificate_id" in data
