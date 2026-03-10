import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from src.models.event import LiveEvent
from src.models.user import User

@pytest.fixture
async def seed_event_data(db_session: AsyncSession):
    start = datetime.utcnow() - timedelta(days=1)
    end = datetime.utcnow() + timedelta(days=1)
    event = LiveEvent(id=1, name="Test Event", start_time=start, end_time=end)
    db_session.add(event)

    # Add User 1
    user1 = User(id=1, name="User1")
    db_session.add(user1)
    # Add User 2
    user2 = User(id=2, name="User2")
    db_session.add(user2)

    await db_session.commit()
    return event

@pytest.mark.asyncio
async def test_active_events(client: AsyncClient, seed_event_data):
    response = await client.get("/events/active")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1

@pytest.mark.asyncio
async def test_play_event(client: AsyncClient, seed_event_data):
    response = await client.post(
        "/events/1/play",
        json={"points": 100},
        headers={"X-User-ID": "1"}
    )
    assert response.status_code == 200
    assert response.json()["points_added"] == 100

@pytest.mark.asyncio
async def test_ranking(client: AsyncClient, seed_event_data):
    # User 1 plays
    await client.post("/events/1/play", json={"points": 100}, headers={"X-User-ID": "1"})
    # User 2 plays more
    await client.post("/events/1/play", json={"points": 200}, headers={"X-User-ID": "2"})

    # Get Ranking
    response = await client.get("/events/1/ranking")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    # Expect User 2 first (rank 1), User 1 second (rank 2)
    assert data[0]["user_id"] == 2
    assert data[0]["score"] == 200
    assert data[0]["rank"] == 1

    assert data[1]["user_id"] == 1
    assert data[1]["score"] == 100
    assert data[1]["rank"] == 2
