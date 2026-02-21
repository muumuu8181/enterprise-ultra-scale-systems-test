import pytest
from httpx import AsyncClient
from sqlalchemy import select
from datetime import datetime
from src.models.tournament_models import Tournament, Team, TournamentFormat, TournamentStatus

@pytest.mark.asyncio
async def test_create_tournament(client: AsyncClient, db_session):
    response = await client.post("/api/v1/tournaments/create", json={
        "game_id": "game1",
        "name": "Summer Championship",
        "format": "single_elim",
        "max_participants": 16,
        "entry_fee": 100.0,
        "prize_pool": 1000.0,
        "start_date": "2024-07-01T10:00:00"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Summer Championship"
    assert data["status"] == "registration"

    # Verify DB
    result = await db_session.execute(select(Tournament).where(Tournament.id == data["id"]))
    tournament = result.scalar_one()
    assert tournament.name == "Summer Championship"

@pytest.mark.asyncio
async def test_list_tournaments(client: AsyncClient, db_session):
    # Create a tournament first
    t = Tournament(
        game_id="game2",
        name="Winter Cup",
        format=TournamentFormat.double_elim,
        max_participants=8,
        entry_fee=50.0,
        prize_pool=500.0,
        status=TournamentStatus.registration,
        start_date=datetime(2024, 12, 1, 10, 0, 0)
    )

    db_session.add(t)
    await db_session.commit()

    response = await client.get("/api/v1/tournaments")
    assert response.status_code == 200
    data = response.json()
    # Filter to find our tournament in case others exist
    found = [d for d in data if d["name"] == "Winter Cup"]
    assert len(found) == 1

@pytest.mark.asyncio
async def test_register_team(client: AsyncClient, db_session):
    # Setup
    t = Tournament(
        game_id="game_reg",
        name="Reg Cup",
        format=TournamentFormat.single_elim,
        max_participants=2,
        entry_fee=0,
        prize_pool=0,
        status=TournamentStatus.registration,
        start_date=datetime(2024, 12, 1, 10, 0, 0)
    )
    team = Team(
        name="Team A",
        captain_id=1,
        members=[{"id": 1, "name": "Player1"}],
        region="NA"
    )
    db_session.add(t)
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(t)
    await db_session.refresh(team)

    # Register
    response = await client.post(f"/api/v1/tournaments/{t.id}/register", json={"team_id": team.id})
    assert response.status_code == 200
    assert response.json() == {"message": "Team registered"}

    # Verify (need to refresh or query again)
    # Note: refresh might not see updates committed in another session if isolation level is high,
    # but here client and db_session share the same DB engine (sqlite memory).
    # However, client requests run in a separate async task/request context.
    # The `client` fixture in conftest overrides `get_db` to yield `db_session`.
    # So they share the SAME session object.
    # Thus, changes made by API are in `db_session` but explicit commit/refresh might be needed.
    # The API calls `db.commit()`.
    # So `db_session` (which is `db`) is committed.
    # We should expire/refresh `t` and `team`.
    await db_session.refresh(t)
    await db_session.refresh(team)

    assert t.participants == [team.id]
    assert len(team.tournament_history) == 1
    assert team.tournament_history[0]["tournament_id"] == t.id

    # Test duplicate registration
    response = await client.post(f"/api/v1/tournaments/{t.id}/register", json={"team_id": team.id})
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]
