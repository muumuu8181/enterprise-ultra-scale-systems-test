from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class CollabSession(Base):
    __tablename__ = 'collab_sessions'

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, index=True, nullable=False)
    active_users = Column(JSON, default=list)  # Store list of user IDs or user objects
    created_at = Column(DateTime, default=datetime.utcnow)

class CollabComment(Base):
    __tablename__ = 'collab_comments'

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, index=True, nullable=False)
    user_id = Column(String, nullable=False)
    anchor_position = Column(JSON)  # Can store range, selection, etc.
    content = Column(String, nullable=False)
    resolved = Column(Boolean, default=False)
    thread_id = Column(String, index=True, nullable=True)

class CollabNotification(Base):
    __tablename__ = 'collab_notifications'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    doc_id = Column(String, nullable=False)
    notif_type = Column(String, nullable=False)  # mention, comment, edit
    read = Column(Boolean, default=False)
