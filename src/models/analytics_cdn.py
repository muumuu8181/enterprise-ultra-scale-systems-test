from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class ViewSession(Base):
    __tablename__ = "view_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    content_id: Mapped[str] = mapped_column(String, index=True)
    edge_node_id: Mapped[str] = mapped_column(String)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    buffering_events: Mapped[int] = mapped_column(Integer, default=0)
    avg_bitrate_kbps: Mapped[int] = mapped_column(Integer)
    quality_switches: Mapped[int] = mapped_column(Integer, default=0)

class CDNMetric(Base):
    __tablename__ = "cdn_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    edge_node_id: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    requests_per_sec: Mapped[float] = mapped_column(Float)
    bandwidth_gbps: Mapped[float] = mapped_column(Float)
    cache_hit_pct: Mapped[float] = mapped_column(Float)
    error_rate: Mapped[float] = mapped_column(Float)

class ABRDecision(Base):
    __tablename__ = "abr_decisions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("view_sessions.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    from_bitrate: Mapped[int] = mapped_column(Integer)
    to_bitrate: Mapped[int] = mapped_column(Integer)
    trigger: Mapped[str] = mapped_column(String) # buffer_low/bandwidth_change
