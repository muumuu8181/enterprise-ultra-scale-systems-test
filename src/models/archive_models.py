from enum import Enum as PyEnum
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base

class ItemType(str, PyEnum):
    DOCUMENT = "document"
    PHOTO = "photo"
    AUDIO = "audio"
    VIDEO = "video"
    THREE_D_SCAN = "3d_scan"

class Condition(str, PyEnum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class ArchiveItem(Base):
    __tablename__ = "archive_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    item_type: Mapped[ItemType]
    date_created: Mapped[datetime]
    origin: Mapped[str] = mapped_column(String(255))
    condition: Mapped[Condition]
    digitized: Mapped[bool] = mapped_column(Boolean, default=False)

    digitization_record: Mapped[Optional["Digitization"]] = relationship(back_populates="item", uselist=False, cascade="all, delete-orphan")

class Digitization(Base):
    __tablename__ = "digitizations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("archive_items.id"), unique=True)
    scan_resolution: Mapped[str] = mapped_column(String(100))
    color_depth: Mapped[str] = mapped_column(String(50))
    file_format: Mapped[str] = mapped_column(String(20))
    file_size_mb: Mapped[float]
    digitized_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    equipment: Mapped[str] = mapped_column(String(255))

    item: Mapped["ArchiveItem"] = relationship(back_populates="digitization_record")

class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    owner_institution: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    public_access: Mapped[bool] = mapped_column(Boolean, default=True)
    license: Mapped[Optional[str]] = mapped_column(String(100))
