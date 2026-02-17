import pytest
from src.models.support_models import TicketPriority, TicketStatus

@pytest.mark.asyncio
async def test_create_ticket(client):
    response = await client.post("/api/v1/tickets", json={
        "subject": "Test Ticket",
        "description": "This is a test ticket",
        "category": "support",
        "priority": "high",
        "customer_id": 123
    })
    assert response.status_code == 200
    data = response.json()
    assert data["subject"] == "Test Ticket"
    assert data["priority"] == "high"
    assert data["status"] == "open"
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_get_ticket(client):
    # Create a ticket first
    create_response = await client.post("/api/v1/tickets", json={
        "subject": "Test Ticket 2",
        "description": "Another test",
        "category": "billing",
        "customer_id": 456
    })
    ticket_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/tickets/{ticket_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == ticket_id
    assert data["subject"] == "Test Ticket 2"

@pytest.mark.asyncio
async def test_create_ticket_message(client):
    create_response = await client.post("/api/v1/tickets", json={
        "subject": "Message Test",
        "description": "Testing messages",
        "category": "tech",
        "customer_id": 789
    })
    ticket_id = create_response.json()["id"]

    response = await client.post(f"/api/v1/tickets/{ticket_id}/messages", json={
        "sender_id": 100,
        "content": "Hello world",
        "attachments": {"file": "log.txt"}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hello world"
    assert data["ticket_id"] == ticket_id
    assert data["attachments"]["file"] == "log.txt"

@pytest.mark.asyncio
async def test_update_ticket_status(client):
    create_response = await client.post("/api/v1/tickets", json={
        "subject": "Status Test",
        "description": "Testing status update",
        "category": "tech",
        "customer_id": 999
    })
    ticket_id = create_response.json()["id"]

    response = await client.put(f"/api/v1/tickets/{ticket_id}/status", json={
        "status": "in_progress"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"

@pytest.mark.asyncio
async def test_get_ticket_queue(client):
    # Create tickets with different attributes
    await client.post("/api/v1/tickets", json={
        "subject": "Queue Test 1", "description": "d", "category": "c", "customer_id": 1, "priority": "high"
    })

    response = await client.get("/api/v1/tickets/queue?priority=high")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["priority"] == "high"

    response = await client.get("/api/v1/tickets/queue?status=open")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["status"] == "open"
