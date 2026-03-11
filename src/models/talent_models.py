from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum, JSON, create_engine
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
import enum
import datetime
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/talent_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Availability(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    FREELANCE = "freelance"

class ProjectStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    SHORTLISTED = "shortlisted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class TalentProfile(Base):
    __tablename__ = "talent_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    skills = Column(JSON)
    experience_years = Column(Integer)
    availability = Column(Enum(Availability), nullable=False)
    hourly_rate = Column(Float)
    portfolio_url = Column(String)
    verified = Column(Boolean, default=False)
    rating = Column(Float, default=0.0)

    applications = relationship("Application", back_populates="talent")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, index=True)
    title = Column(String)
    description = Column(String)
    required_skills = Column(JSON)
    budget_range = Column(String)
    duration_weeks = Column(Integer)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.OPEN)

    applications = relationship("Application", back_populates="project")

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    talent_id = Column(Integer, ForeignKey("talent_profiles.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    cover_letter = Column(String)
    proposed_rate = Column(Float)
    proposed_timeline = Column(String)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.APPLIED)
    applied_at = Column(DateTime, default=datetime.datetime.utcnow)

    talent = relationship("TalentProfile", back_populates="applications")
    project = relationship("Project", back_populates="applications")
