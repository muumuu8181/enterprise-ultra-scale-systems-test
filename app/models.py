from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, create_engine, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone

Base = declarative_base()

class Election(Base):
    __tablename__ = "elections"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    candidates = relationship("Candidate", back_populates="election")
    votes = relationship("Vote", back_populates="election")

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    election_id = Column(Integer, ForeignKey("elections.id"))

    election = relationship("Election", back_populates="candidates")
    votes = relationship("Vote", back_populates="candidate")

class Voter(Base):
    __tablename__ = "voters"
    id = Column(Integer, primary_key=True, index=True)
    hashed_id = Column(String, unique=True, index=True) # SHA-256(salt + real_id)

class VoterParticipation(Base):
    __tablename__ = "voter_participation"
    id = Column(Integer, primary_key=True, index=True)
    voter_id = Column(Integer, ForeignKey("voters.id"), nullable=False)
    election_id = Column(Integer, ForeignKey("elections.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint('voter_id', 'election_id', name='uq_voter_election'),
    )

class Vote(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(Integer, ForeignKey("elections.id"))
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    election = relationship("Election", back_populates="votes")
    candidate = relationship("Candidate", back_populates="votes")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Database Setup
DATABASE_URL = "sqlite:///./election.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
