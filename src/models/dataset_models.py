from datetime import datetime, timezone
from typing import List, Any
from sqlalchemy import String, Integer, BigInteger, JSON, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[str] = mapped_column(String)
    storage_path: Mapped[str] = mapped_column(String)
    schema: Mapped[dict[str, Any]] = mapped_column(JSON)
    row_count: Mapped[int] = mapped_column(BigInteger)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    tags: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    splits: Mapped[List["DatasetSplit"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")

class DatasetSplit(Base):
    __tablename__ = "dataset_splits"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))
    split_type: Mapped[str] = mapped_column(String)
    storage_path: Mapped[str] = mapped_column(String)
    row_count: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    dataset: Mapped["Dataset"] = relationship(back_populates="splits")
