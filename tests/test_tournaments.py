import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fastapi import FastAPI
from src.models.tournament_models import Base
from src.api.v1.tournaments import router, get_db

# Setup App
app = FastAPI()
app.include_router(router, prefix="/api/v1")

# Setup Test DB
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_tournament_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Tournament
        response = await ac.post("/api/v1/tournaments/", json={
            "name": "Test Tournament",
            "format": "single_elimination",
            "max_participants": 4
        })
        assert response.status_code == 201
        data = response.json()
        tournament_id = data["id"]
        assert data["status"] == "scheduled"

        # 2. Register Participants
        user_ids = [101, 102, 103, 104]
        for uid in user_ids:
            response = await ac.post(f"/api/v1/tournaments/{tournament_id}/register", json={"user_id": uid})
            assert response.status_code == 200

        # 3. Start Tournament
        response = await ac.post(f"/api/v1/tournaments/{tournament_id}/start")
        assert response.status_code == 200

        # 4. Get Bracket
        response = await ac.get(f"/api/v1/tournaments/{tournament_id}/bracket")
        assert response.status_code == 200
        bracket = response.json()

        # Should have 4 participants -> 3 matches (2 in round 1, 1 in round 2)
        assert len(bracket) == 3

        round1_matches = [m for m in bracket if m["round"] == 1]
        assert len(round1_matches) == 2

        # 5. Report Round 1 Matches
        m1 = round1_matches[0]
        m2 = round1_matches[1]

        # Need to know which players are in m1/m2
        # m1 and m2 should have valid players
        assert m1["player1_id"] is not None
        assert m1["player2_id"] is not None
        assert m2["player1_id"] is not None
        assert m2["player2_id"] is not None

        winner1 = m1["player1_id"]
        response = await ac.post(f"/api/v1/tournaments/{tournament_id}/matches/{m1['id']}/report", json={
            "winner_id": winner1,
            "score_a": 10,
            "score_b": 5
        })
        assert response.status_code == 200

        winner2 = m2["player2_id"]
        response = await ac.post(f"/api/v1/tournaments/{tournament_id}/matches/{m2['id']}/report", json={
            "winner_id": winner2,
            "score_a": 2,
            "score_b": 8
        })
        assert response.status_code == 200

        # 6. Verify Final Match Populated
        response = await ac.get(f"/api/v1/tournaments/{tournament_id}/bracket")
        bracket = response.json()
        final_match = next(m for m in bracket if m["round"] == 2)

        # Check if updated
        assert final_match["player1_id"] == winner1
        assert final_match["player2_id"] == winner2

        # 7. Report Final Match
        final_winner = winner1
        response = await ac.post(f"/api/v1/tournaments/{tournament_id}/matches/{final_match['id']}/report", json={
            "winner_id": final_winner,
            "score_a": 3,
            "score_b": 2
        })
        assert response.status_code == 200

        # 8. Get Standings
        response = await ac.get(f"/api/v1/tournaments/{tournament_id}/standings")
        assert response.status_code == 200
        standings = response.json()

        # Rank 1: final_winner
        r1 = next(s for s in standings if s["rank"] == 1)
        assert r1["user_id"] == final_winner

        # Rank 2: loser of final (winner2)
        r2 = next(s for s in standings if s["rank"] == 2)
        assert r2["user_id"] == winner2

        # Rank 3: losers of round 1 (shared)
        r3s = [s for s in standings if s["rank"] == 3]
        assert len(r3s) == 2
