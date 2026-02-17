import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_scout_report(client: AsyncClient):
    payload = {
        "scout_id": "scout_001",
        "player_id": "player_123",
        "skills": {"dribbling": 85, "passing": 90},
        "physical_ratings": {"speed": 88, "stamina": 92},
        "recommendation": "Must Buy",
        "market_value_estimate": 25000000.0
    }
    response = await client.post("/api/v1/scouts/reports", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["scout_id"] == "scout_001"
    assert data["recommendation"] == "Must Buy"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_player_reports(client: AsyncClient):
    # First create a report
    payload = {
        "scout_id": "scout_002",
        "player_id": "player_456",
        "skills": {},
        "physical_ratings": {},
        "recommendation": "Watch",
        "market_value_estimate": 5000000.0
    }
    await client.post("/api/v1/scouts/reports", json=payload)

    response = await client.get("/api/v1/players/player_456/scout-reports")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["player_id"] == "player_456"

@pytest.mark.asyncio
async def test_find_similar_players(client: AsyncClient):
    payload = {
        "budget": 10000000.0,
        "position": "Forward"
    }
    response = await client.post("/api/v1/analytics/similar-players/player_789", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "similar_players" in data
    assert len(data["similar_players"]) > 0

@pytest.mark.asyncio
async def test_market_value_history(client: AsyncClient):
    response = await client.get("/api/v1/players/player_999/market-value-history")
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == "player_999"
    assert "history" in data
