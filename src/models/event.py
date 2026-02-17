from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class LiveEvent(Base):
    __tablename__ = "live_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    points: Mapped[list["EventPoint"]] = relationship("EventPoint", back_populates="event", cascade="all, delete-orphan")


class EventPoint(Base):
    __tablename__ = "event_points"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("live_events.id"), primary_key=True)
    point: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    event: Mapped["LiveEvent"] = relationship("LiveEvent", back_populates="points")
