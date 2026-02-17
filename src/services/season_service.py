from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from src.models.season_models import Season, SeasonStage, UserSeason
from src.models.user import User

class SeasonService:
    async def get_current_season(self, db: AsyncSession) -> Season | None:
        """
        現在のシーズンを取得
        Get current active season
        """
        now = datetime.utcnow()
        query = select(Season).where(Season.start_date <= now, Season.end_date >= now)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_season_stages(self, db: AsyncSession, season_id: int) -> list[SeasonStage]:
        """
        シーズンの全ステージを取得
        Get all stages for a season
        """
        query = select(SeasonStage).where(SeasonStage.season_id == season_id).order_by(SeasonStage.stage_number)
        result = await db.execute(query)
        return result.scalars().all()

    async def add_season_xp(self, db: AsyncSession, user_id: int, season_id: int, xp: int) -> UserSeason:
        """
        シーズンXPを追加
        Add Season XP
        """
        query = select(UserSeason).where(UserSeason.user_id == user_id, UserSeason.season_id == season_id)
        result = await db.execute(query)
        user_season = result.scalars().first()

        if not user_season:
            # Create entry if not exists
            user_season = UserSeason(
                user_id=user_id,
                season_id=season_id,
                current_xp=0,
                is_premium=False,
                completed_stages=[]
            )
            db.add(user_season)

        user_season.current_xp += xp
        await db.commit()
        await db.refresh(user_season)
        return user_season

    async def check_stage_unlock(self, db: AsyncSession, user_season: UserSeason) -> list[int]:
        """
        ロック解除されたステージ番号のリストを返す
        Returns list of unlocked stage numbers
        """
        query = select(SeasonStage).where(SeasonStage.season_id == user_season.season_id).order_by(SeasonStage.stage_number)
        result = await db.execute(query)
        stages = result.scalars().all()

        unlocked = []
        for stage in stages:
            if user_season.current_xp >= stage.required_xp:
                unlocked.append(stage.stage_number)
        return unlocked

    async def claim_reward(self, db: AsyncSession, user_id: int, season_id: int, stage_number: int):
        """
        報酬を受け取る
        Claim reward for a specific stage
        """
        # Get UserSeason
        query = select(UserSeason).where(UserSeason.user_id == user_id, UserSeason.season_id == season_id)
        result = await db.execute(query)
        user_season = result.scalars().first()
        if not user_season:
            raise HTTPException(status_code=404, detail="User season progress not found")

        # Get Stage
        query_stage = select(SeasonStage).where(SeasonStage.season_id == season_id, SeasonStage.stage_number == stage_number)
        result_stage = await db.execute(query_stage)
        stage = result_stage.scalars().first()
        if not stage:
            raise HTTPException(status_code=404, detail="Stage not found")

        # Check XP requirement
        if user_season.current_xp < stage.required_xp:
             raise HTTPException(status_code=400, detail="Not enough XP")

        # Check if already claimed
        if stage_number in user_season.completed_stages:
             raise HTTPException(status_code=400, detail="Reward already claimed")

        # Prepare Reward
        rewards = []
        if stage.free_reward:
            rewards.append(stage.free_reward)

        if user_season.is_premium and stage.premium_reward:
            rewards.append(stage.premium_reward)

        # Grant rewards (Currency only implementation for now)
        if rewards:
            user = await db.get(User, user_id)
            if user:
                for reward in rewards:
                    # Check if reward is dictionary and has 'item' key
                    if isinstance(reward, dict) and reward.get("item") == "coin":
                        amount = reward.get("amount", 0)
                        if isinstance(amount, int):
                            user.currency += amount

        # Update claimed status (Create new list to ensure SQLAlchemy detects change)
        new_list = list(user_season.completed_stages)
        new_list.append(stage_number)
        user_season.completed_stages = new_list

        await db.commit()
        return rewards

    async def purchase_pass(self, db: AsyncSession, user_id: int, season_id: int) -> UserSeason:
        """
        プレミアムパス購入
        Purchase Premium Pass
        """
        # Get User
        user = await db.get(User, user_id)
        if not user:
             raise HTTPException(status_code=404, detail="User not found")

        # Get Season
        season = await db.get(Season, season_id)
        if not season:
             raise HTTPException(status_code=404, detail="Season not found")

        # Get UserSeason
        query = select(UserSeason).where(UserSeason.user_id == user_id, UserSeason.season_id == season_id)
        result = await db.execute(query)
        user_season = result.scalars().first()

        if user_season and user_season.is_premium:
             raise HTTPException(status_code=400, detail="Already premium")

        # Check Currency
        if user.currency < season.premium_price:
             raise HTTPException(status_code=400, detail="Insufficient currency")

        # Deduct Currency
        user.currency -= season.premium_price

        # Enable Premium
        if not user_season:
            user_season = UserSeason(
                user_id=user_id,
                season_id=season_id,
                current_xp=0,
                is_premium=True,
                completed_stages=[]
            )
            db.add(user_season)
        else:
            user_season.is_premium = True

        await db.commit()
        await db.refresh(user_season)
        return user_season
