import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.story_models import Chapter, Stage, UserStageProgress
from src.models.user import User

@pytest.fixture
async def seed_story_data(db_session: AsyncSession):
    # User
    user = User(id=1, name="TestUser", currency=1000)
    db_session.add(user)

    # Chapters
    c1 = Chapter(id=1, title="Chapter 1", order=1, unlock_conditions=None)
    c2 = Chapter(id=2, title="Chapter 2", order=2, unlock_conditions=None)
    db_session.add_all([c1, c2])
    await db_session.commit()

    # Stages for C1
    # s1_1: Score > 100 for star
    s1_1 = Stage(id=1, chapter_id=1, title="Stage 1-1", order=1, difficulty=1, star_conditions={"min_score": 100})
    # s1_2: Time < 60 for star
    s1_2 = Stage(id=2, chapter_id=1, title="Stage 1-2", order=2, difficulty=1, star_conditions={"time_limit": 60})

    # Stages for C2
    s2_1 = Stage(id=3, chapter_id=2, title="Stage 2-1", order=1, difficulty=2)

    db_session.add_all([s1_1, s1_2, s2_1])
    await db_session.commit()

@pytest.mark.asyncio
async def test_get_chapters(client: AsyncClient, seed_story_data):
    response = await client.get("/story/chapters", headers={"X-User-ID": "1"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Chapter 1"

@pytest.mark.asyncio
async def test_get_stages_locked(client: AsyncClient, seed_story_data):
    # Chapter 2 should be locked initially because C1 not cleared
    # Logic: unlock_chapter checks if previous chapter's stages are cleared.

    response = await client.get("/story/chapters/2/stages", headers={"X-User-ID": "1"})
    assert response.status_code == 403
    assert "locked" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_stages_unlocked(client: AsyncClient, seed_story_data):
    # Chapter 1 is always unlocked
    response = await client.get("/story/chapters/1/stages", headers={"X-User-ID": "1"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

@pytest.mark.asyncio
async def test_complete_stage_and_unlock(client: AsyncClient, seed_story_data, db_session):
    # Complete 1-1
    # Condition: min_score 100. Let's get 2 stars (clear + score).
    resp = await client.post(
        "/story/stages/1/complete",
        json={"score": 150, "time_sec": 100},
        headers={"X-User-ID": "1"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cleared"] is True
    assert data["stars"] == 2 # 1 base + 1 score

    # Check progress in DB
    prog = await db_session.get(UserStageProgress, data["id"])
    assert prog.cleared is True

    # C2 still locked? Need to clear 1-2.
    resp = await client.get("/story/chapters/2/stages", headers={"X-User-ID": "1"})
    assert resp.status_code == 403

    # Complete 1-2
    # Condition: time_limit 60.
    resp = await client.post(
        "/story/stages/2/complete",
        json={"score": 0, "time_sec": 50},
        headers={"X-User-ID": "1"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["stars"] == 2 # 1 base + 1 time

    # Now C2 should be unlocked
    resp = await client.get("/story/chapters/2/stages", headers={"X-User-ID": "1"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == 3

@pytest.mark.asyncio
async def test_progress_endpoint(client: AsyncClient, seed_story_data):
    # Clear 1-1
    await client.post(
        "/story/stages/1/complete",
        json={"score": 200, "time_sec": 10},
        headers={"X-User-ID": "1"}
    )

    resp = await client.get("/story/progress/1", headers={"X-User-ID": "1"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["progress"]) == 1
    assert data["progress"][0]["stage_id"] == 1
    assert data["progress"][0]["cleared"] is True
