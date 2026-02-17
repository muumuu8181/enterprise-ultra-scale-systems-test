import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User

@pytest.mark.asyncio
async def test_create_guild(client: AsyncClient, db_session: AsyncSession):
    # Create user
    user = User(name="Leader", currency=100)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create guild
    response = await client.post(
        "/guilds/",
        json={"name": "TestGuild", "description": "Best guild"},
        headers={"x-user-id": str(user.id)}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "TestGuild"
    assert data["leader_id"] == user.id
    assert data["members_count"] == 1

@pytest.mark.asyncio
async def test_join_guild(client: AsyncClient, db_session: AsyncSession):
    # Create 2 users
    u1 = User(name="Leader", currency=100)
    u2 = User(name="Member", currency=100)
    db_session.add_all([u1, u2])
    await db_session.commit()
    await db_session.refresh(u1)
    await db_session.refresh(u2)

    # U1 creates guild
    r1 = await client.post(
        "/guilds/",
        json={"name": "TestGuild"},
        headers={"x-user-id": str(u1.id)}
    )
    assert r1.status_code == 200
    guild_id = r1.json()["id"]

    # U2 joins
    r2 = await client.post(
        f"/guilds/{guild_id}/join",
        headers={"x-user-id": str(u2.id)}
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["user_id"] == u2.id
    assert data["guild_id"] == guild_id

    # Verify members count
    r3 = await client.get(f"/guilds/{guild_id}")
    assert r3.json()["members_count"] == 2

    # Verify members list
    r4 = await client.get(f"/guilds/{guild_id}/members")
    assert len(r4.json()) == 2

@pytest.mark.asyncio
async def test_start_battle(client: AsyncClient, db_session: AsyncSession):
    # Create 2 users (leaders)
    u1 = User(name="L1")
    u2 = User(name="L2")
    db_session.add_all([u1, u2])
    await db_session.commit()
    await db_session.refresh(u1)
    await db_session.refresh(u2)

    # Create 2 guilds
    g1_resp = await client.post("/guilds/", json={"name": "G1"}, headers={"x-user-id": str(u1.id)})
    g1_id = g1_resp.json()["id"]

    g2_resp = await client.post("/guilds/", json={"name": "G2"}, headers={"x-user-id": str(u2.id)})
    g2_id = g2_resp.json()["id"]

    # Start battle (u1 starts vs g2)
    b_resp = await client.post(
        f"/guilds/{g1_id}/battle",
        json={"opponent_guild_id": g2_id},
        headers={"x-user-id": str(u1.id)}
    )
    assert b_resp.status_code == 200
    data = b_resp.json()
    assert data["guild_a_id"] == g1_id
    assert data["guild_b_id"] == g2_id
    assert data["scores"] == {"guild_a": 0, "guild_b": 0}

@pytest.mark.asyncio
async def test_leave_and_promote(client: AsyncClient, db_session: AsyncSession):
    # U1 (Leader), U2 (Member), U3 (Member)
    u1 = User(name="L")
    u2 = User(name="M1")
    u3 = User(name="M2")
    db_session.add_all([u1, u2, u3])
    await db_session.commit()
    await db_session.refresh(u1)

    # Create Guild
    r = await client.post("/guilds/", json={"name": "G"}, headers={"x-user-id": str(u1.id)})
    assert r.status_code == 200
    g_id = r.json()["id"]

    # Join
    await client.post(f"/guilds/{g_id}/join", headers={"x-user-id": str(u2.id)})
    await client.post(f"/guilds/{g_id}/join", headers={"x-user-id": str(u3.id)})

    # Promote U2
    p_resp = await client.put(f"/guilds/{g_id}/promote?target_user_id={u2.id}", headers={"x-user-id": str(u1.id)})
    assert p_resp.status_code == 200

    # Verify role
    m_resp = await client.get(f"/guilds/{g_id}/members")
    members = m_resp.json()
    u2_member = next(m for m in members if m["user_id"] == u2.id)
    assert u2_member["role"] == "vice_leader"

    # U3 Leaves
    l_resp = await client.delete(f"/guilds/{g_id}/leave", headers={"x-user-id": str(u3.id)})
    assert l_resp.status_code == 200

    # Verify count
    g_resp = await client.get(f"/guilds/{g_id}")
    assert g_resp.json()["members_count"] == 2 # U1 + U2
