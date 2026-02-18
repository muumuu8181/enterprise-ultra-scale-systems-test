import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.inventory_models import Item, UserInventory, TradeOffer
from src.models.user import User

@pytest.fixture
async def seed_inventory_data(db_session: AsyncSession):
    user1 = User(id=1, name="User1", currency=1000)
    user2 = User(id=2, name="User2", currency=500)
    db_session.add(user1)
    db_session.add(user2)

    item1 = Item(id=1, name="Potion", rarity=1, type="consumable", stats={"hp": 50})
    item2 = Item(id=2, name="Sword", rarity=3, type="weapon", stats={"atk": 10})
    db_session.add(item1)
    db_session.add(item2)
    await db_session.flush()

    inv1 = UserInventory(user_id=1, item_id=1, quantity=10)
    inv2 = UserInventory(user_id=1, item_id=2, quantity=1)
    db_session.add(inv1)
    db_session.add(inv2)

    await db_session.commit()
    # Ensure fresh state
    # await db_session.refresh(user1)
    return user1, user2, item1, item2

@pytest.mark.asyncio
async def test_get_inventory(client: AsyncClient, seed_inventory_data):
    response = await client.get("/inventory/1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Order isn't guaranteed
    potion = next(i for i in data if i["item"]["name"] == "Potion")
    assert potion["quantity"] == 10
    assert potion["item"]["rarity"] == 1

@pytest.mark.asyncio
async def test_use_item(client: AsyncClient, seed_inventory_data, db_session):
    response = await client.post(
        "/inventory/use",
        json={"item_id": 1, "quantity": 1},
        headers={"X-User-ID": "1"}
    )
    assert response.status_code == 200

    # Check DB
    stmt = select(UserInventory).where(UserInventory.user_id == 1, UserInventory.item_id == 1)
    result = await db_session.execute(stmt)
    inv = result.scalar_one()
    assert inv.quantity == 9

@pytest.mark.asyncio
async def test_sell_item(client: AsyncClient, seed_inventory_data, db_session):
    response = await client.post(
        "/inventory/sell",
        json={"item_id": 1, "quantity": 5, "price": 100},
        headers={"X-User-ID": "1"}
    )
    assert response.status_code == 200

    # Check DB Inventory
    stmt = select(UserInventory).where(UserInventory.user_id == 1, UserInventory.item_id == 1)
    result = await db_session.execute(stmt)
    inv = result.scalar_one()
    assert inv.quantity == 5 # 10 - 5

    # Check DB User Currency
    user = await db_session.get(User, 1)
    assert user.currency == 1100 # 1000 + 100

@pytest.mark.asyncio
async def test_create_trade(client: AsyncClient, seed_inventory_data, db_session):
    response = await client.post(
        "/inventory/trade",
        json={
            "target_user_id": 2,
            "offer": {"2": 1}, # Sword (User 1 has 1)
            "request": {"1": 5} # 5 Potions (User 2 has 0, but request is valid)
        },
        headers={"X-User-ID": "1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"

    # Check DB Item Lock
    stmt = select(UserInventory).where(UserInventory.user_id == 1, UserInventory.item_id == 2)
    result = await db_session.execute(stmt)
    inv = result.scalar_one()
    assert inv.is_locked is True

@pytest.mark.asyncio
async def test_create_trade_insufficient(client: AsyncClient, seed_inventory_data):
    response = await client.post(
        "/inventory/trade",
        json={
            "target_user_id": 2,
            "offer": {"1": 20}, # 20 Potions (User 1 has 10)
            "request": {"1": 5}
        },
        headers={"X-User-ID": "1"}
    )
    assert response.status_code == 400
