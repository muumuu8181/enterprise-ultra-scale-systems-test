import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User

@pytest.mark.asyncio
async def test_friend_request_flow(client: AsyncClient, db_session: AsyncSession):
    # 1. Create Users
    user1 = User(name="Alice", currency=1000)
    user2 = User(name="Bob", currency=1000)
    db_session.add_all([user1, user2])
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    # 2. Send Friend Request (Alice -> Bob)
    response = await client.post(
        "/social/friends/request",
        json={"target_user_id": user2.id},
        headers={"x-user-id": str(user1.id)}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["from_user_id"] == user1.id
    assert data["to_user_id"] == user2.id
    assert data["status"] == "pending"
    request_id = data["id"]

    # 3. Accept Friend Request (Bob accepts)
    response = await client.put(
        f"/social/friends/request/{request_id}/accept",
        headers={"x-user-id": str(user2.id)}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"

    # 4. List Friends
    # Check Alice's friends
    response = await client.get(
        f"/social/friends/{user1.id}",
        headers={"x-user-id": str(user1.id)}
    )
    assert response.status_code == 200
    friends = response.json()
    assert len(friends) == 1
    assert friends[0]["user_id"] == user2.id
    assert friends[0]["name"] == "Bob"

    # Check Bob's friends
    response = await client.get(
        f"/social/friends/{user2.id}",
        headers={"x-user-id": str(user2.id)}
    )
    assert response.status_code == 200
    friends = response.json()
    assert len(friends) == 1
    assert friends[0]["user_id"] == user1.id

@pytest.mark.asyncio
async def test_gift_sending(client: AsyncClient, db_session: AsyncSession):
    # Setup users
    user1 = User(name="Charlie", currency=1000)
    user2 = User(name="Dave", currency=1000)
    db_session.add_all([user1, user2])
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    # Create friendship via API
    req_resp = await client.post(
        "/social/friends/request",
        json={"target_user_id": user2.id},
        headers={"x-user-id": str(user1.id)}
    )
    req_id = req_resp.json()["id"]
    await client.put(
        f"/social/friends/request/{req_id}/accept",
        headers={"x-user-id": str(user2.id)}
    )

    # Send Gift (Charlie -> Dave)
    response = await client.post(
        "/social/gifts/send",
        json={"friend_id": user2.id, "item_id": "stamina_potion", "message": "Here is a gift!"},
        headers={"x-user-id": str(user1.id)}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == "stamina_potion"
    assert data["from_user_id"] == user1.id

    # Check Feed for Dave
    response = await client.get(
        f"/social/feed/{user2.id}",
        headers={"x-user-id": str(user2.id)}
    )
    assert response.status_code == 200
    feed = response.json()
    # Expect 2 items: Friendship made, Gift received
    assert len(feed) >= 2
    gift_items = [item for item in feed if item["type"] == "gift_received"]
    assert len(gift_items) == 1
    assert "stamina_potion" in gift_items[0]["content"]

@pytest.mark.asyncio
async def test_remove_friend(client: AsyncClient, db_session: AsyncSession):
    user1 = User(name="Eve", currency=1000)
    user2 = User(name="Frank", currency=1000)
    db_session.add_all([user1, user2])
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    # Create friendship
    req_resp = await client.post(
        "/social/friends/request",
        json={"target_user_id": user2.id},
        headers={"x-user-id": str(user1.id)}
    )
    req_id = req_resp.json()["id"]
    await client.put(
        f"/social/friends/request/{req_id}/accept",
        headers={"x-user-id": str(user2.id)}
    )

    # Verify friend list
    resp = await client.get(f"/social/friends/{user1.id}", headers={"x-user-id": str(user1.id)})
    friend_entry = resp.json()[0]
    friendship_id = friend_entry["id"]

    # Remove friend
    response = await client.delete(
        f"/social/friends/{friendship_id}",
        headers={"x-user-id": str(user1.id)}
    )
    assert response.status_code == 200

    # Verify empty list
    resp = await client.get(f"/social/friends/{user1.id}", headers={"x-user-id": str(user1.id)})
    assert len(resp.json()) == 0
