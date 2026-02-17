from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, LargeBinary
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from geoalchemy2 import Geometry

# Assuming a shared Base exists or defining a local one for this module if none is found.
# Given the instructions, I'll define a Base here to ensure the models are complete.
class Base(AsyncAttrs, DeclarativeBase):
    pass

class MapTile(Base):
    __tablename__ = 'map_tiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    z: Mapped[int] = mapped_column(Integer, nullable=False)
    x: Mapped[int] = mapped_column(Integer, nullable=False)
    y: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

class RoadCondition(Base):
    __tablename__ = 'road_conditions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    road_id: Mapped[str] = mapped_column(String, nullable=False)
    condition_type: Mapped[str] = mapped_column(String, nullable=False)  # e.g., 'wet', 'dry', 'ice', 'construction'
    location: Mapped[str] = mapped_column(Geometry('POINT'), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=True)
