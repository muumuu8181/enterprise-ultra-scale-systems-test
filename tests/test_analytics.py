import pytest
from src.models.support_models import Ticket, TicketStatus, Agent
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_ticket_volume(client, db_session):
    # Seed data
    t1 = Ticket(user_id="u1", created_at=datetime.utcnow(), status=TicketStatus.OPEN)
    t2 = Ticket(user_id="u2", created_at=datetime.utcnow(), status=TicketStatus.CLOSED)
    db_session.add_all([t1, t2])
    await db_session.commit()

    res = await client.get("/api/v1/analytics/ticket-volume")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 2

@pytest.mark.asyncio
async def test_resolution_time(client, db_session):
    # Seed data
    created = datetime.utcnow() - timedelta(hours=2)
    resolved = datetime.utcnow()
    t1 = Ticket(user_id="u1", created_at=created, resolved_at=resolved, status=TicketStatus.RESOLVED)
    db_session.add(t1)
    await db_session.commit()

    res = await client.get("/api/v1/analytics/resolution-time")
    assert res.status_code == 200
    data = res.json()
    # Should be approx 2 hours
    assert 1.9 <= data["average_resolution_hours"] <= 2.1

@pytest.mark.asyncio
async def test_agent_performance(client, db_session):
    # Create agents
    a1 = Agent(name="Alice", email="alice@test.com")
    a2 = Agent(name="Bob", email="bob@test.com")
    db_session.add_all([a1, a2])
    await db_session.commit()
    await db_session.refresh(a1)
    await db_session.refresh(a2)

    # Create resolved ticket for Alice
    t1 = Ticket(user_id="u1", status=TicketStatus.RESOLVED, assigned_agent_id=a1.id)
    db_session.add(t1)
    await db_session.commit()

    res = await client.get("/api/v1/analytics/agent-performance")
    assert res.status_code == 200
    data = res.json()

    alice = next(d for d in data if d["agent"] == "Alice")
    bob = next(d for d in data if d["agent"] == "Bob")

    assert alice["resolved_tickets"] == 1
    assert bob["resolved_tickets"] == 0
