import pytest
from src.models.collab_models import DocType, OpType

@pytest.mark.asyncio
async def test_create_document(async_client):
    response = await async_client.post("/documents/create", json={
        "title": "Test Doc",
        "owner_id": 1,
        "doc_type": "text"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Doc"
    assert data["id"] is not None
    assert data["owner_id"] == 1

@pytest.mark.asyncio
async def test_apply_operation(async_client):
    # Create doc
    response = await async_client.post("/documents/create", json={
        "title": "Test Doc",
        "owner_id": 1,
        "doc_type": "text"
    })
    doc_id = response.json()["id"]

    # Apply op
    op_response = await async_client.post(f"/documents/{doc_id}/operations", json={
        "user_id": 2,
        "op_type": "insert",
        "position": 0,
        "content": "Hello"
    })
    assert op_response.status_code == 200
    assert op_response.json()["applied"] is True

    # Check snapshot
    snap_response = await async_client.get(f"/documents/{doc_id}/snapshot")
    assert snap_response.status_code == 200
    assert snap_response.json()["content"] == "Hello"

@pytest.mark.asyncio
async def test_ot_logic(async_client):
    # Create doc
    response = await async_client.post("/documents/create", json={
        "title": "OT Doc",
        "owner_id": 1,
        "doc_type": "text"
    })
    doc_id = response.json()["id"]

    # Simple sequential ops
    await async_client.post(f"/documents/{doc_id}/operations", json={
        "user_id": 1, "op_type": "insert", "position": 0, "content": "A"
    })
    await async_client.post(f"/documents/{doc_id}/operations", json={
        "user_id": 2, "op_type": "insert", "position": 1, "content": "B"
    })

    snap = await async_client.get(f"/documents/{doc_id}/snapshot")
    assert snap.json()["content"] == "AB"

@pytest.mark.asyncio
async def test_share_document(async_client):
    response = await async_client.post("/documents/create", json={
        "title": "Shared Doc",
        "owner_id": 1,
        "doc_type": "text"
    })
    doc_id = response.json()["id"]

    # Use query param for user_id
    share_resp = await async_client.post(f"/documents/{doc_id}/share", params={"user_id": 2})
    assert share_resp.status_code == 200

    collabs = await async_client.get(f"/documents/{doc_id}/collaborators")
    assert 2 in collabs.json()["collaborators"]
