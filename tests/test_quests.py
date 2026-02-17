import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.quest_models import Quest, QuestType
from src.models.user import User

# Helper to seed quests
async def seed_quests(db: AsyncSession):
    # Daily Quest
    q1 = Quest(
        type=QuestType.DAILY,
        title="Daily Login",
        description="Log in once",
        conditions={"target_count": 1},
        rewards={"currency": 100},
        reset_interval="daily"
    )
    # Weekly Quest
    q2 = Quest(
        type=QuestType.WEEKLY,
        title="Weekly Challenge",
        description="Do 5 pulls",
        conditions={"target_count": 5},
        rewards={"currency": 500},
        reset_interval="weekly"
    )
    db.add_all([q1, q2])
    await db.commit()
    await db.refresh(q1)
    await db.refresh(q2)
    return q1, q2

@pytest.mark.asyncio
async def test_get_daily_quests(client: AsyncClient, db_session: AsyncSession):
    await seed_quests(db_session)

    response = await client.get("/quests/daily", headers={"x-user-id": "1"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Daily Login"
    assert data[0]["status"] == "inactive"

@pytest.mark.asyncio
async def test_accept_quest(client: AsyncClient, db_session: AsyncSession):
    q1, _ = await seed_quests(db_session)
    q1_id = q1.id # Capture ID before it gets expired by subsequent commits

    user = User(id=1, name="Test User", currency=0)
    db_session.add(user)
    await db_session.commit()

    response = await client.post(f"/quests/{q1_id}/accept", headers={"x-user-id": "1"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"

    # Verify persistence
    response = await client.get("/quests/daily", headers={"x-user-id": "1"})
    data = response.json()
    assert data[0]["status"] == "accepted"

@pytest.mark.asyncio
async def test_progress_quest(client: AsyncClient, db_session: AsyncSession):
    q1, _ = await seed_quests(db_session)
    q1_id = q1.id

    user = User(id=1, name="Test User", currency=0)
    db_session.add(user)
    await db_session.commit()

    # Accept first
    await client.post(f"/quests/{q1_id}/accept", headers={"x-user-id": "1"})

    # Progress
    response = await client.post(
        f"/quests/{q1_id}/progress",
        json={"increment": 1},
        headers={"x-user-id": "1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["progress"]["current_count"] == 1
    assert data["status"] == "completed" # Target is 1

@pytest.mark.asyncio
async def test_complete_quest(client: AsyncClient, db_session: AsyncSession):
    q1, _ = await seed_quests(db_session)
    q1_id = q1.id

    user = User(id=1, name="Test User", currency=0)
    db_session.add(user)
    await db_session.commit()

    # Accept & Complete
    await client.post(f"/quests/{q1_id}/accept", headers={"x-user-id": "1"})
    await client.post(f"/quests/{q1_id}/progress", json={"increment": 1}, headers={"x-user-id": "1"})

    # Claim
    response = await client.post(f"/quests/{q1_id}/complete", headers={"x-user-id": "1"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["rewards"]["currency"] == 100

    # Verify currency added
    await db_session.refresh(user)
    assert user.currency == 100

    # Verify status claimed
    response = await client.get("/quests/daily", headers={"x-user-id": "1"})
    data = response.json()
    assert data[0]["status"] == "claimed"

@pytest.mark.asyncio
async def test_complete_incomplete_quest(client: AsyncClient, db_session: AsyncSession):
    q1, _ = await seed_quests(db_session)
    q1_id = q1.id

    user = User(id=1, name="Test User", currency=0)
    db_session.add(user)
    await db_session.commit()

    await client.post(f"/quests/{q1_id}/accept", headers={"x-user-id": "1"})
    # No progress

    response = await client.post(f"/quests/{q1_id}/complete", headers={"x-user-id": "1"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Quest not completed yet"
