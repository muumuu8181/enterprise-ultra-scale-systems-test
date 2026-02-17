import uuid
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis
from src.models.pvp_models import Match, PlayerRating, MatchMode, MatchStatus

class MatchmakingService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.k_factor = 32

    async def add_to_queue(self, user_id: int, mode: MatchMode):
        # Get user rating
        rating = await self.get_user_rating(user_id, mode)
        # Add to sorted set: key=pvp:queue:{mode}, score=rating, member=user_id
        await self.redis.zadd(f"pvp:queue:{mode.value}", {str(user_id): rating})

    async def remove_from_queue(self, user_id: int, mode: MatchMode):
        await self.redis.zrem(f"pvp:queue:{mode.value}", str(user_id))

    async def find_match(self, user_id: int, mode: MatchMode):
        rating = await self.get_user_rating(user_id, mode)
        min_rating = rating - 200
        max_rating = rating + 200

        # Find candidates
        # We need to exclude self.
        candidates = await self.redis.zrangebyscore(f"pvp:queue:{mode.value}", min_rating, max_rating)

        opponent_id = None
        for cid in candidates:
            if cid == str(user_id):
                continue

            # Try to claim this opponent (atomic check not fully implemented here, assuming simple flow)
            # In a real system, we'd use a lock or atomic transaction
            opponent_id = int(cid)
            break

        if opponent_id:
            # Remove both from queue
            await self.remove_from_queue(user_id, mode)
            await self.remove_from_queue(opponent_id, mode)
            return await self.create_match(user_id, opponent_id, mode)

        return None

    async def create_match(self, player1_id: int, player2_id: int, mode: MatchMode) -> Match:
        match_id = str(uuid.uuid4())
        match = Match(
            id=match_id,
            player1_id=player1_id,
            player2_id=player2_id,
            mode=mode,
            status=MatchStatus.ACTIVE,
            created_at=datetime.utcnow()
        )
        self.db.add(match)
        await self.db.commit()
        await self.db.refresh(match)
        return match

    async def get_user_rating(self, user_id: int, mode: MatchMode) -> int:
        stmt = select(PlayerRating).where(PlayerRating.user_id == user_id, PlayerRating.mode == mode)
        result = await self.db.execute(stmt)
        rating_obj = result.scalar_one_or_none()

        if not rating_obj:
            # Create default rating
            rating_obj = PlayerRating(user_id=user_id, mode=mode, elo_rating=1200)
            self.db.add(rating_obj)
            await self.db.commit()
            await self.db.refresh(rating_obj)

        return rating_obj.elo_rating

    async def calculate_elo_change(self, match: Match):
        if not match.winner_id:
            return

        stmt_p1 = select(PlayerRating).where(PlayerRating.user_id == match.player1_id, PlayerRating.mode == match.mode)
        stmt_p2 = select(PlayerRating).where(PlayerRating.user_id == match.player2_id, PlayerRating.mode == match.mode)

        res1 = await self.db.execute(stmt_p1)
        res2 = await self.db.execute(stmt_p2)

        p1_rating = res1.scalar_one()
        p2_rating = res2.scalar_one()

        r1 = p1_rating.elo_rating
        r2 = p2_rating.elo_rating

        # Expected scores
        e1 = 1 / (1 + 10 ** ((r2 - r1) / 400))
        e2 = 1 / (1 + 10 ** ((r1 - r2) / 400))

        s1 = 1 if match.winner_id == match.player1_id else 0
        s2 = 1 if match.winner_id == match.player2_id else 0

        # New ratings
        new_r1 = r1 + self.k_factor * (s1 - e1)
        new_r2 = r2 + self.k_factor * (s2 - e2)

        p1_rating.elo_rating = int(new_r1)
        p2_rating.elo_rating = int(new_r2)

        # Update stats
        if s1 == 1:
            p1_rating.wins += 1
            p2_rating.losses += 1
        else:
            p1_rating.losses += 1
            p2_rating.wins += 1

        self.db.add(p1_rating)
        self.db.add(p2_rating)
        await self.db.commit()
