from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.metaverse_models import Avatar, VirtualSpace

class ProximityEvent(BaseModel):
    avatar_id: int
    target_id: int
    distance: float
    event_type: str = "proximity"

class SpatialService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_avatar_position(self, avatar_id: int, x: float, y: float, z: float, space_id: int):
        stmt = select(Avatar).where(Avatar.id == avatar_id)
        result = await self.db.execute(stmt)
        avatar = result.scalar_one_or_none()

        if not avatar:
            return None

        old_space_id = avatar.current_space_id

        if old_space_id != space_id:
            # Handle leaving old space
            if old_space_id is not None:
                stmt_old = select(VirtualSpace).where(VirtualSpace.id == old_space_id)
                res_old = await self.db.execute(stmt_old)
                old_space = res_old.scalar_one_or_none()
                if old_space and old_space.current_users > 0:
                    old_space.current_users -= 1

            # Handle entering new space
            stmt_new = select(VirtualSpace).where(VirtualSpace.id == space_id)
            res_new = await self.db.execute(stmt_new)
            new_space = res_new.scalar_one_or_none()

            if new_space:
                if new_space.current_users >= new_space.max_occupancy:
                    raise ValueError("Space is full")
                new_space.current_users += 1

        avatar.position_x = x
        avatar.position_y = y
        avatar.position_z = z
        avatar.current_space_id = space_id

        await self.db.commit()
        await self.db.refresh(avatar)
        return avatar

    async def detect_proximity_events(self, space_id: int, threshold: float = 5.0) -> list[ProximityEvent]:
        # Simple N^2 check for demo purposes
        stmt = select(Avatar).where(Avatar.current_space_id == space_id)
        result = await self.db.execute(stmt)
        avatars = result.scalars().all()

        events = []
        for i, a1 in enumerate(avatars):
            for a2 in avatars[i+1:]:
                dist = ((a1.position_x - a2.position_x)**2 +
                        (a1.position_y - a2.position_y)**2 +
                        (a1.position_z - a2.position_z)**2) ** 0.5

                if dist <= threshold:
                    events.append(ProximityEvent(
                        avatar_id=a1.id,
                        target_id=a2.id,
                        distance=dist
                    ))
                    events.append(ProximityEvent(
                        avatar_id=a2.id,
                        target_id=a1.id,
                        distance=dist
                    ))
        return events
