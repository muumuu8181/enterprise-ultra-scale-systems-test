import pytest
from sqlalchemy import select
from src.models.achievement_models import Achievement, UserAchievement
from src.services.achievement_service import achievement_service

@pytest.mark.asyncio
async def test_unlock_on_first_gacha(db_session):
    ach = Achievement(
        name="First Pull",
        description="First gacha",
        conditions={"type": "gacha_pull", "target": 1}
    )
    db_session.add(ach)
    await db_session.flush()

    user_id = 1

    await achievement_service.on_gacha_pull(db_session, user_id, 1)
    await db_session.flush()

    result = await db_session.execute(select(UserAchievement).where(UserAchievement.achievement_id == ach.id))
    ua = result.scalar_one_or_none()

    assert ua is not None
    assert ua.unlocked_at is not None
    assert ua.progress["current"] == 1

@pytest.mark.asyncio
async def test_pvp_win_streak(db_session):
    ach = Achievement(
        name="Duelist",
        description="Win 3 PvP",
        conditions={"type": "pvp_win", "target": 3}
    )
    db_session.add(ach)
    await db_session.flush()

    user_id = 1

    # Win 1
    await achievement_service.on_pvp_win(db_session, user_id)
    await db_session.flush()
    result = await db_session.execute(select(UserAchievement).where(UserAchievement.achievement_id == ach.id))
    ua = result.scalar_one()
    assert ua.unlocked_at is None
    assert ua.progress["current"] == 1

    # Win 2
    await achievement_service.on_pvp_win(db_session, user_id)
    await db_session.flush()

    # Win 3
    await achievement_service.on_pvp_win(db_session, user_id)
    await db_session.flush()

    # Should unlock
    result = await db_session.execute(select(UserAchievement).where(UserAchievement.achievement_id == ach.id))
    ua = result.scalar_one()
    assert ua.unlocked_at is not None
    assert ua.progress["current"] == 3

@pytest.mark.asyncio
async def test_full_completion(db_session):
    ach1 = Achievement(name="A1", description="D1", conditions={"type": "t1", "target": 1})
    ach2 = Achievement(name="A2", description="D2", conditions={"type": "t2", "target": 1})
    db_session.add_all([ach1, ach2])
    await db_session.flush()

    user_id = 1

    rate = await achievement_service.calculate_completion_rate(db_session, user_id)
    assert rate == 0.0

    await achievement_service.unlock_achievement(db_session, user_id, ach1.id)
    await db_session.flush()
    rate = await achievement_service.calculate_completion_rate(db_session, user_id)
    assert rate == 50.0

    await achievement_service.unlock_achievement(db_session, user_id, ach2.id)
    await db_session.flush()
    rate = await achievement_service.calculate_completion_rate(db_session, user_id)
    assert rate == 100.0
