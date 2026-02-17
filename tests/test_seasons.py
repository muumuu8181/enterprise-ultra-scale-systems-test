import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from src.models.season_models import Season, SeasonStage, UserSeason
from src.models.user import User

@pytest.fixture
async def seed_season_data(db_session: AsyncSession):
    # Create User
    user = User(id=1, name="SeasonUser", currency=1000)
    db_session.add(user)

    # Create Active Season
    start = datetime.utcnow() - timedelta(days=1)
    end = datetime.utcnow() + timedelta(days=30)
    season = Season(
        id=1, name="Season 1", start_date=start, end_date=end,
        max_stages=10, premium_price=500
    )
    db_session.add(season)

    # Create Stages
    stage1 = SeasonStage(
        season_id=1, stage_number=1, required_xp=100,
        free_reward={"item": "coin", "amount": 100},
        premium_reward={"item": "gem", "amount": 10}
    )
    stage2 = SeasonStage(
        season_id=1, stage_number=2, required_xp=300,
        free_reward={"item": "coin", "amount": 200},
        premium_reward={"item": "gem", "amount": 20}
    )
    db_session.add_all([stage1, stage2])

    await db_session.commit()
    return season

@pytest.mark.asyncio
async def test_get_current_season(client: AsyncClient, seed_season_data):
    response = await client.get("/seasons/current")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Season 1"

@pytest.mark.asyncio
async def test_purchase_pass_success(client: AsyncClient, seed_season_data, db_session):
    response = await client.post(
        "/seasons/purchase-pass",
        headers={"X-User-ID": "1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_premium"] is True

    # Check DB
    await db_session.refresh(await db_session.get(User, 1))
    user = await db_session.get(User, 1)
    assert user.currency == 500  # 1000 - 500

@pytest.mark.asyncio
async def test_purchase_pass_insufficient_funds(client: AsyncClient, seed_season_data, db_session):
    # Update user currency
    user = await db_session.get(User, 1)
    user.currency = 100
    await db_session.commit()

    response = await client.post(
        "/seasons/purchase-pass",
        headers={"X-User-ID": "1"}
    )
    assert response.status_code == 400
    assert "Insufficient currency" in response.json()["detail"]

@pytest.mark.asyncio
async def test_claim_reward_free(client: AsyncClient, seed_season_data, db_session):
    # Setup: Add UserSeason with XP
    user_season = UserSeason(
        user_id=1, season_id=1, current_xp=150, is_premium=False, completed_stages=[]
    )
    db_session.add(user_season)
    await db_session.commit()

    response = await client.post(
        "/seasons/stages/1/claim",
        headers={"X-User-ID": "1"}
    )
    assert response.status_code == 200
    data = response.json()
    rewards = data["rewards"]
    assert len(rewards) == 1
    assert rewards[0]["item"] == "coin"

    # Check DB
    await db_session.refresh(user_season)
    assert 1 in user_season.completed_stages

    # Check currency increase (1000 initial + 100 reward)
    await db_session.refresh(await db_session.get(User, 1))
    user = await db_session.get(User, 1)
    assert user.currency == 1100

@pytest.mark.asyncio
async def test_claim_reward_premium(client: AsyncClient, seed_season_data, db_session):
    # Setup: Add UserSeason with XP and Premium
    user_season = UserSeason(
        user_id=1, season_id=1, current_xp=150, is_premium=True, completed_stages=[]
    )
    db_session.add(user_season)
    await db_session.commit()

    response = await client.post(
        "/seasons/stages/1/claim",
        headers={"X-User-ID": "1"}
    )
    assert response.status_code == 200
    data = response.json()
    rewards = data["rewards"]
    assert len(rewards) == 2
    # Check for both coin and gem
    items = [r["item"] for r in rewards]
    assert "coin" in items
    assert "gem" in items

@pytest.mark.asyncio
async def test_claim_locked_stage(client: AsyncClient, seed_season_data, db_session):
    # XP 150, trying to claim stage 2 (req 300)
    user_season = UserSeason(
        user_id=1, season_id=1, current_xp=150, is_premium=False, completed_stages=[]
    )
    db_session.add(user_season)
    await db_session.commit()

    response = await client.post(
        "/seasons/stages/2/claim",
        headers={"X-User-ID": "1"}
    )
    assert response.status_code == 400
    assert "Not enough XP" in response.json()["detail"]
