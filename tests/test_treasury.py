import pytest
import datetime
from src.models.treasury_models import AssetType, GrantStatus, TransactionType, TreasuryAsset, MultisigTransaction
from src.services.treasury_service import calculate_runway

@pytest.mark.asyncio
async def test_get_treasury_assets(client, db_session):
    # Seed data
    asset = TreasuryAsset(
        dao_id="dao1",
        asset_type=AssetType.STABLECOIN,
        token_address="0x123",
        balance=1000.0,
        usd_value=1000.0,
        last_updated=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    )
    db_session.add(asset)
    await db_session.commit()

    response = await client.get("/api/v1/daos/dao1/treasury")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["dao_id"] == "dao1"
    assert data[0]["usd_value"] == 1000.0

@pytest.mark.asyncio
async def test_create_grant_application(client, db_session):
    payload = {
        "dao_id": "dao1",
        "applicant_address": "0xabc",
        "requested_amount": 5000.0,
        "description": "Project Alpha",
        "milestones": [
            {"id": 1, "description": "Phase 1", "amount": 2000.0},
            {"id": 2, "description": "Phase 2", "amount": 3000.0}
        ]
    }
    response = await client.post("/api/v1/grants/apply", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == GrantStatus.SUBMITTED
    assert len(data["milestones"]) == 2

    # Check status endpoint
    grant_id = data["id"]
    response = await client.get(f"/api/v1/grants/{grant_id}/status")
    assert response.status_code == 200
    assert response.json()["status"] == GrantStatus.SUBMITTED

@pytest.mark.asyncio
async def test_multisig_workflow(client, db_session):
    # Seed Multisig Transaction
    tx = MultisigTransaction(
        dao_id="dao1",
        tx_type=TransactionType.PAYMENT,
        amount=100.0,
        recipient="0xrecipient",
        signers_required=2,
        signatures=[],
        executed=False
    )
    db_session.add(tx)
    await db_session.commit()
    await db_session.refresh(tx)
    tx_id = tx.id

    # Check pending
    response = await client.get("/api/v1/daos/dao1/multisig/pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == tx_id

    # Sign 1
    payload1 = {"signer_address": "0xsig1", "signature": "sig1"}
    response = await client.post(f"/api/v1/multisig/{tx_id}/sign", json=payload1)
    assert response.status_code == 200
    data = response.json()
    assert len(data["signatures"]) == 1
    assert data["executed"] == False

    # Sign 2
    payload2 = {"signer_address": "0xsig2", "signature": "sig2"}
    response = await client.post(f"/api/v1/multisig/{tx_id}/sign", json=payload2)
    assert response.status_code == 200
    data = response.json()
    assert len(data["signatures"]) == 2
    assert data["executed"] == True

@pytest.mark.asyncio
async def test_calculate_runway_logic(db_session):
    # Seed assets
    asset1 = TreasuryAsset(dao_id="dao2", asset_type=AssetType.STABLECOIN, usd_value=20000.0)
    asset2 = TreasuryAsset(dao_id="dao2", asset_type=AssetType.TOKEN, usd_value=50000.0) # Should be ignored
    db_session.add_all([asset1, asset2])
    await db_session.commit()

    result = await calculate_runway("dao2", db_session)
    # Burn rate is mocked at 10000.0
    assert result["total_stable_usd"] == 20000.0
    assert result["runway_months"] == 2.0
