from datetime import datetime
from typing import Any, Dict, List

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class VectorCollection(Base):
    __tablename__ = "vector_collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    dimension: Mapped[int] = mapped_column(Integer)
    metric: Mapped[str] = mapped_column(String)  # cosine, euclidean, dot
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    items: Mapped[List["VectorItem"]] = relationship(
        "VectorItem", back_populates="collection", cascade="all, delete-orphan"
    )


class VectorItem(Base):
    __tablename__ = "vector_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("vector_collections.id"), index=True
    )
    external_id: Mapped[str] = mapped_column(String, index=True)
    # Dimension is dynamic per collection, so we use Vector(None) or just Vector
    embedding: Mapped[Any] = mapped_column(Vector(None))
    # Using JSONB for better performance and indexing capabilities
    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default={})

    collection: Mapped["VectorCollection"] = relationship(
        "VectorCollection", back_populates="items"
    )
