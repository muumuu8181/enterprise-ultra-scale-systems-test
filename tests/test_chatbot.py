import pytest

@pytest.mark.asyncio
async def test_create_session(client):
    response = await client.post("/api/v1/chatbot/sessions", json={"user_id": "user1"})
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user1"
    assert "id" in data

@pytest.mark.asyncio
async def test_send_message(client):
    # Create session
    res = await client.post("/api/v1/chatbot/sessions", json={"user_id": "user1"})
    session_id = res.json()["id"]

    # Send message
    res = await client.post(f"/api/v1/chatbot/sessions/{session_id}/messages", json={"content": "hello"})
    assert res.status_code == 200
    data = res.json()
    assert "response" in data

@pytest.mark.asyncio
async def test_escalate(client):
    res = await client.post("/api/v1/chatbot/sessions", json={"user_id": "user1"})
    session_id = res.json()["id"]

    res = await client.post(f"/api/v1/chatbot/sessions/{session_id}/escalate", json={"reason": "need help"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "escalated"
