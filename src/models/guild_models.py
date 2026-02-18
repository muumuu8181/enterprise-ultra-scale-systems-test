from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Guild(Base):
    """
    ギルドモデル
    """
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    leader_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    exp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_members: Mapped[int] = mapped_column(Integer, default=10, nullable=False) # max_members from request
    members_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False) # initially just the leader
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    members: Mapped[List["GuildMember"]] = relationship("GuildMember", back_populates="guild", cascade="all, delete-orphan")
    battles_as_a: Mapped[List["GuildBattle"]] = relationship("GuildBattle", foreign_keys="[GuildBattle.guild_a_id]", back_populates="guild_a")
    battles_as_b: Mapped[List["GuildBattle"]] = relationship("GuildBattle", foreign_keys="[GuildBattle.guild_b_id]", back_populates="guild_b")

class GuildMember(Base):
    """
    ギルドメンバーモデル
    """
    __tablename__ = "guild_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True) # User can only be in one guild
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False) # 'leader', 'vice_leader', 'member'
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    contribution_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    guild: Mapped["Guild"] = relationship("Guild", back_populates="members")
    # user relationship is optional but good to have if we query member -> user
    # user: Mapped["User"] = relationship("User")

class GuildBattle(Base):
    """
    ギルドバトルモデル
    """
    __tablename__ = "guild_battles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_a_id: Mapped[int] = mapped_column(ForeignKey("guilds.id"), nullable=False)
    guild_b_id: Mapped[int] = mapped_column(ForeignKey("guilds.id"), nullable=False)
    winner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("guilds.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    guild_a: Mapped["Guild"] = relationship("Guild", foreign_keys=[guild_a_id], back_populates="battles_as_a")
    guild_b: Mapped["Guild"] = relationship("Guild", foreign_keys=[guild_b_id], back_populates="battles_as_b")
