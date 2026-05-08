import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from src.models.gacha import GachaBanner, GachaRate
from src.models.user import User
from src.services.gacha_service import GachaService
from unittest.mock import patch

@pytest.fixture
async def seed_gacha_data(db_session: AsyncSession, redis_client):
    # Create User
    user = User(id=1, name="TestUser", currency=10000)
    db_session.add(user)

    # Create Banner
    start = datetime.utcnow() - timedelta(days=1)
    end = datetime.utcnow() + timedelta(days=1)
    banner = GachaBanner(
        id=1, name="Standard Banner", pool_type="standard",
        start_time=start, end_time=end
    )
    db_session.add(banner)

    # Create Rates
    rates = [
        GachaRate(banner_id=1, item_id="item_5_1", rarity=5, weight=10, is_pickup=True),
        GachaRate(banner_id=1, item_id="item_4_1", rarity=4, weight=100, is_pickup=True),
        GachaRate(banner_id=1, item_id="item_3_1", rarity=3, weight=890, is_pickup=False),
    ]
    db_session.add_all(rates)
    await db_session.commit()

    # Set Redis Currency
    await redis_client.set("user:1:currency", 10000)

    return banner

@pytest.mark.asyncio
async def test_gacha_pull_single(client: AsyncClient, seed_gacha_data):
    response = await client.post(
        "/gacha/pull",
        json={"banner_id": 1, "count": 1},
        headers={"X-Request-ID": "req1", "X-User-ID": "1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["currency_remaining"] == 9900  # 10000 - 100

@pytest.mark.asyncio
async def test_gacha_pull_multi(client: AsyncClient, seed_gacha_data):
    response = await client.post(
        "/gacha/pull",
        json={"banner_id": 1, "count": 10},
        headers={"X-Request-ID": "req2", "X-User-ID": "1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 10
    assert data["currency_remaining"] == 9000

@pytest.mark.asyncio
async def test_insufficient_currency(client: AsyncClient, seed_gacha_data, redis_client):
    await redis_client.set("user:1:currency", 50)
    response = await client.post(
        "/gacha/pull",
        json={"banner_id": 1, "count": 1},
        headers={"X-Request-ID": "req3", "X-User-ID": "1"}
    )
    assert response.status_code == 400
    assert "Insufficient currency" in response.json()["detail"]

@pytest.mark.asyncio
async def test_idempotency(client: AsyncClient, seed_gacha_data):
    # First request
    response1 = await client.post(
        "/gacha/pull",
        json={"banner_id": 1, "count": 1},
        headers={"X-Request-ID": "req_dup", "X-User-ID": "1"}
    )
    assert response1.status_code == 200

    # Second request with same ID
    response2 = await client.post(
        "/gacha/pull",
        json={"banner_id": 1, "count": 1},
        headers={"X-Request-ID": "req_dup", "X-User-ID": "1"}
    )
    # Should return 409 Conflict as per implementation
    assert response2.status_code == 409

@pytest.mark.asyncio
async def test_pity_increment(client: AsyncClient, seed_gacha_data, db_session):
    # Force miss (0.9 > 0.6% and > 5.1%)
    with patch("src.services.gacha_service.random.random", side_effect=[0.9, 0.9]):
        await client.post(
            "/gacha/pull",
            json={"banner_id": 1, "count": 1},
            headers={"X-Request-ID": "req_pity_inc", "X-User-ID": "1"}
        )

    # Check DB pity counter
    from src.models.gacha import UserPityCounter
    pity = await db_session.get(UserPityCounter, (1, "standard"))
    assert pity is not None
    assert pity.pity_count == 1

@pytest.mark.asyncio
async def test_pity_reset_on_5_star(client: AsyncClient, seed_gacha_data, db_session):
    # Set initial pity to something high to ensure it resets, or just check 0
    # Create existing pity
    from src.models.gacha import UserPityCounter
    pity_record = UserPityCounter(user_id=1, pool_type="standard", pity_count=10)
    db_session.add(pity_record)
    await db_session.commit()

    # Force 5* hit (0.0 < prob)
    # Also need to mock randint for item selection if select_item uses it.
    # But select_item uses randint(1, total_weight). We don't patch randint, only random.random.
    with patch("src.services.gacha_service.random.random", return_value=0.0):
        response = await client.post(
            "/gacha/pull",
            json={"banner_id": 1, "count": 1},
            headers={"X-Request-ID": "req_pity_reset", "X-User-ID": "1"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["rarity"] == 5

    # Check pity reset
    await db_session.refresh(pity_record)
    assert pity_record.pity_count == 0

@pytest.mark.asyncio
async def test_currency_db_fallback(client: AsyncClient, seed_gacha_data, redis_client, db_session):
    # Delete Redis key to simulate cache miss
    await redis_client.delete("user:1:currency")

    # DB has 10000 (from seed)

    # Request pull
    response = await client.post(
        "/gacha/pull",
        json={"banner_id": 1, "count": 1},
        headers={"X-Request-ID": "req_fallback", "X-User-ID": "1"}
    )
    assert response.status_code == 200

    # Redis should be repopulated with 10000 - 100 = 9900
    val = await redis_client.get("user:1:currency")
    assert val is not None
    assert int(val) == 9900

    # DB should be updated
    from src.models.user import User
    await db_session.refresh(await db_session.get(User, 1))
    user = await db_session.get(User, 1)
    assert user.currency == 9900
