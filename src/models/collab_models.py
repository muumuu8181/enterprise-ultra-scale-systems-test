from sqlalchemy import Column, Integer, String, Enum, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from src.db.base import Base
import enum

class DocType(str, enum.Enum):
    text = "text"
    spreadsheet = "spreadsheet"
    whiteboard = "whiteboard"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    owner_id = Column(Integer, nullable=False)
    doc_type = Column(Enum(DocType), nullable=False)
    version = Column(Integer, default=0)
    last_modified = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    collaborators = Column(JSON, default=list)

class OpType(str, enum.Enum):
    insert = "insert"
    delete = "delete"
    format = "format"

class DocumentOperation(Base):
    __tablename__ = "document_operations"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    op_type = Column(Enum(OpType), nullable=False)
    position = Column(Integer, nullable=False)
    content = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    applied = Column(Boolean, default=False)

class PresenceInfo(Base):
    __tablename__ = "presence_info"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    cursor_position = Column(Integer, nullable=True)
    selection = Column(JSON, nullable=True)
    color = Column(String, nullable=True)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
