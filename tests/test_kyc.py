import pytest
from httpx import AsyncClient
from src.models.kyc_models import KYCStatus

@pytest.mark.asyncio
async def test_submit_kyc_success(client: AsyncClient):
    """KYC申請の正常系テスト"""
    payload = {
        "customer_id": "cust_001",
        "name": "John Doe",
        "dob": "1990-01-01",
        "address": "123 Main St",
        "id_number": "ID12345"
    }
    response = await client.post("/kyc/submit", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["customer_id"] == "cust_001"
    assert data["status"] == KYCStatus.PENDING
    assert "id" in data

@pytest.mark.asyncio
async def test_get_kyc_status(client: AsyncClient):
    """KYCステータス取得テスト"""
    # 事前に申請を作成
    payload = {
        "customer_id": "cust_002",
        "name": "Jane Doe",
        "dob": "1992-02-02",
        "address": "456 Side St",
        "id_number": "ID67890"
    }
    await client.post("/kyc/submit", json=payload)

    # ステータス取得
    response = await client.get("/kyc/status/cust_002")
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "cust_002"
    assert data["status"] == KYCStatus.PENDING

@pytest.mark.asyncio
async def test_verify_kyc_approve(client: AsyncClient):
    """KYC申請の承認テスト"""
    # 事前に申請を作成
    payload = {
        "customer_id": "cust_003",
        "name": "Bob Smith",
        "dob": "1985-05-05",
        "address": "789 Up St",
        "id_number": "ID11223"
    }
    await client.post("/kyc/submit", json=payload)

    # 承認リクエスト
    verify_payload = {
        "customer_id": "cust_003",
        "approved": True
    }
    response = await client.put("/kyc/verify", json=verify_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == KYCStatus.VERIFIED
    assert data["verified_at"] is not None

@pytest.mark.asyncio
async def test_verify_kyc_reject(client: AsyncClient):
    """KYC申請の拒否テスト"""
    # 事前に申請を作成
    payload = {
        "customer_id": "cust_004",
        "name": "Alice Cooper",
        "dob": "1970-07-07",
        "address": "321 Down St",
        "id_number": "ID44556"
    }
    await client.post("/kyc/submit", json=payload)

    # 拒否リクエスト
    reject_payload = {
        "customer_id": "cust_004",
        "approved": False,
        "rejection_reason": "Invalid ID"
    }
    response = await client.put("/kyc/verify", json=reject_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == KYCStatus.REJECTED
    assert data["rejection_reason"] == "Invalid ID"
    assert data["verified_at"] is not None

@pytest.mark.asyncio
async def test_get_pending_applications(client: AsyncClient):
    """保留中のKYC申請一覧取得テスト"""
    # 複数の申請を作成
    payload1 = {
        "customer_id": "cust_005",
        "name": "Pending User 1",
        "dob": "2000-01-01",
        "address": "Address 1",
        "id_number": "ID_P1"
    }
    await client.post("/kyc/submit", json=payload1)

    payload2 = {
        "customer_id": "cust_006",
        "name": "Pending User 2",
        "dob": "2000-01-02",
        "address": "Address 2",
        "id_number": "ID_P2"
    }
    await client.post("/kyc/submit", json=payload2)

    # 保留リスト取得
    response = await client.get("/kyc/pending")
    assert response.status_code == 200
    data = response.json()
    # 他のテストの影響を受ける可能性があるため、少なくとも2件以上あることを確認
    # (conftestのscope="function"ならDBはクリアされるはず)
    assert len(data) >= 2
    ids = [item["customer_id"] for item in data]
    assert "cust_005" in ids
    assert "cust_006" in ids
