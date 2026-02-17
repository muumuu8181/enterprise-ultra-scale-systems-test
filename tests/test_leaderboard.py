import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.leaderboard import GlobalLeaderboard
from src.services.scoring import recalculate_rankings

@pytest.mark.asyncio
async def test_submit_score(client: AsyncClient):
    # Test submitting a score
    response = await client.post("/scores/submit", json={
        "player_id": "player1",
        "game_id": "game1",
        "score": 100.0,
        "metadata": {"level": 1}
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

    # Verify stats
    response = await client.get("/players/player1/stats?game_id=game1")
    assert response.status_code == 200
    data = response.json()
    assert data["highest_score"] == 100.0
    assert data["percentile"] == 0.0

@pytest.mark.asyncio
async def test_leaderboard_logic(client: AsyncClient, db_session: AsyncSession):
    # Submit multiple scores
    await client.post("/scores/submit", json={"player_id": "p1", "game_id": "g1", "score": 100})
    await client.post("/scores/submit", json={"player_id": "p2", "game_id": "g1", "score": 200})

    # Get leaderboard ID manually to trigger recalculation
    result = await db_session.execute(select(GlobalLeaderboard).where(GlobalLeaderboard.game_id == "g1"))
    lb = result.scalars().first()
    assert lb is not None

    # Recalculate rankings directly (simulating celery task)
    await recalculate_rankings(db_session, lb.id)

    # Check leaderboard via API (using alltime period since submit_score creates alltime by default)
    response = await client.get("/leaderboards/g1/global?period=alltime")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # p2 should be first (score 200)
    assert data[0]["player_id"] == "p2"
    assert data[0]["score"] == 200.0
    assert data[0]["rank"] == 1

    # p1 should be second (score 100)
    assert data[1]["player_id"] == "p1"
    assert data[1]["score"] == 100.0
    assert data[1]["rank"] == 2

    # Verify Percentile for p2 (Rank 1/2 -> 50%)
    response = await client.get("/players/p2/stats?game_id=g1")
    data = response.json()
    assert data["percentile"] == 50.0

    # Verify Percentile for p1 (Rank 2/2 -> 0%)
    response = await client.get("/players/p1/stats?game_id=g1")
    data = response.json()
    assert data["percentile"] == 0.0
