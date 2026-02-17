from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.models.v2x_models import Base, utcnow

class PlatoonGroup(Base):
    """
    队形走行グループモデル
    Platoon Group Model
    """
    __tablename__ = "platoon_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    leader_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="forming") # forming, active, dissolving
    target_speed: Mapped[float] = mapped_column(Float)
    spacing_distance: Mapped[float] = mapped_column(Float)
    member_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class PlatoonMember(Base):
    """
    队形走行メンバーモデル
    Platoon Member Model
    """
    __tablename__ = "platoon_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("platoon_groups.id"), index=True)
    vehicle_id: Mapped[str] = mapped_column(String, index=True)
    position_in_platoon: Mapped[int] = mapped_column(Integer)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
