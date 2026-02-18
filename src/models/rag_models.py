from datetime import datetime, timezone
from typing import List, Optional, Any
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    """
    SQLAlchemyのベースクラス
    SQLAlchemy Base Class
    """
    pass

class Document(Base):
    """
    RAG用ドキュメントモデル
    Document model for RAG
    """
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False, comment="ドキュメントのタイトル")
    source_url: Mapped[Optional[str]] = mapped_column(String, nullable=True, comment="ソースURL")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, comment="チャンク数")
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="取り込み日時"
    )

    chunks: Mapped[List["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    """
    ドキュメントのチャンクモデル
    Document Chunk model
    """
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, comment="チャンクのインデックス")
    text: Mapped[str] = mapped_column(String, nullable=False, comment="チャンクのテキスト内容")
    # 1536次元はOpenAIのtext-embedding-3-smallなどを想定。必要に応じて変更可能。
    embedding: Mapped[Any] = mapped_column(Vector(1536), nullable=True, comment="ベクトル埋め込み")
    metadata_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="メタデータ")

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
