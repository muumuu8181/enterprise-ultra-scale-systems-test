from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Enum as SAEnum, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
import enum
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List

Base = declarative_base()

class ClassStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    LIVE = "live"
    RECORDED = "recorded"

class VirtualClass(Base):
    __tablename__ = "virtual_classes"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(String, index=True)
    title = Column(String)
    subject = Column(String)
    schedule = Column(JSON)
    max_students = Column(Integer)
    status = Column(SAEnum(ClassStatus), default=ClassStatus.UPCOMING)

    enrollments = relationship("Enrollment", back_populates="virtual_class")
    live_sessions = relationship("LiveSession", back_populates="virtual_class")

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("virtual_classes.id"))
    student_id = Column(String, index=True)
    enrolled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completion_pct = Column(Float, default=0.0)
    grade = Column(String, nullable=True)
    certificate_issued = Column(Boolean, default=False)

    virtual_class = relationship("VirtualClass", back_populates="enrollments")

class LiveSession(Base):
    __tablename__ = "live_sessions"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("virtual_classes.id"))
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)
    recording_url = Column(String, nullable=True)
    attendance_count = Column(Integer, default=0)
    chat_log_uri = Column(String, nullable=True)

    virtual_class = relationship("VirtualClass", back_populates="live_sessions")

# Pydantic models
class SessionConfig(BaseModel):
    session_id: int
    streaming_url: str
    token: str
    protocol: str = "webrtc"

    model_config = ConfigDict(from_attributes=True)

class Certificate(BaseModel):
    id: str
    student_id: str
    course_title: str
    issued_at: datetime
    verification_url: str

    model_config = ConfigDict(from_attributes=True)
