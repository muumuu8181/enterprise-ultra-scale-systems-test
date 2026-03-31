from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship, declarative_base
from geoalchemy2 import Geometry
import enum
from datetime import datetime

Base = declarative_base()

class ElectionType(enum.Enum):
    general = "general"
    primary = "primary"
    local = "local"
    referendum = "referendum"

class ElectionStatus(enum.Enum):
    announced = "announced"
    registration = "registration"
    voting = "voting"
    counting = "counting"
    certified = "certified"

class CandidateStatus(enum.Enum):
    registered = "registered"
    qualified = "qualified"
    disqualified = "disqualified"
    elected = "elected"
    defeated = "defeated"

class PollingStationStatus(enum.Enum):
    setup = "setup"
    open = "open"
    closed = "closed"
    reporting = "reporting"

class Election(Base):
    __tablename__ = 'elections'

    id = Column(Integer, primary_key=True)
    election_type = Column(SAEnum(ElectionType), nullable=False)
    jurisdiction = Column(String, nullable=False)
    election_date = Column(DateTime, nullable=False)
    registration_deadline = Column(DateTime, nullable=False)
    status = Column(SAEnum(ElectionStatus), default=ElectionStatus.announced)

    candidates = relationship("Candidate", back_populates="election")
    polling_stations = relationship("PollingStation", back_populates="election")

class Candidate(Base):
    __tablename__ = 'candidates'

    id = Column(Integer, primary_key=True)
    election_id = Column(Integer, ForeignKey('elections.id'), nullable=False)
    name = Column(String, nullable=False)
    party = Column(String)
    position_sought = Column(String, nullable=False)
    manifesto_url = Column(String)
    endorsements = Column(JSON)
    status = Column(SAEnum(CandidateStatus), default=CandidateStatus.registered)

    election = relationship("Election", back_populates="candidates")

class PollingStation(Base):
    __tablename__ = 'polling_stations'

    id = Column(Integer, primary_key=True)
    election_id = Column(Integer, ForeignKey('elections.id'), nullable=False)
    name = Column(String, nullable=False)
    location = Column(Geometry('POINT'), nullable=False)
    capacity = Column(Integer)
    registered_voters = Column(Integer, default=0)
    ballots_cast = Column(Integer, default=0)
    turnout_pct = Column(Float)
    status = Column(SAEnum(PollingStationStatus), default=PollingStationStatus.setup)
    accessibility = Column(JSON)

    election = relationship("Election", back_populates="polling_stations")
