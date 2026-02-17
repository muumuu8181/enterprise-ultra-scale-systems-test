from sqlalchemy import Column, Integer, String, Float, Enum, Date, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class CaseStatus(str, enum.Enum):
    OPEN = "open"
    ESCALATED = "escalated"
    CLOSED = "closed"

class RelationshipType(str, enum.Enum):
    OWNS = "owns"
    CONTROLS = "controls"
    TRANSACTS = "transacts"

class WatchlistType(str, enum.Enum):
    OFAC = "ofac"
    UN = "un"
    EU = "eu"
    LOCAL = "local"

class AMLCase(Base):
    __tablename__ = "aml_cases"

    id = Column(Integer, primary_key=True, index=True)
    sar_id = Column(String, unique=True, index=True)
    analyst_id = Column(String, index=True)
    priority = Column(Integer)  # Higher number = higher priority? Or lower? Assuming standard int
    typology = Column(String)
    estimated_proceeds = Column(Float)
    status = Column(Enum(CaseStatus), default=CaseStatus.OPEN)
    disposition = Column(String)  # e.g., "False Positive", "Reported", etc.

    # Relationships
    entity_links = relationship("EntityLink", back_populates="case")


class EntityLink(Base):
    __tablename__ = "entity_links"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("aml_cases.id"))
    entity1_id = Column(String, index=True)
    entity2_id = Column(String, index=True)
    relationship_type = Column(Enum(RelationshipType))
    evidence = Column(JSON)  # Stores evidence details as JSON

    # Relationships
    case = relationship("AMLCase", back_populates="entity_links")


class WatchlistEntry(Base):
    __tablename__ = "watchlist_entries"

    id = Column(Integer, primary_key=True, index=True)
    list_type = Column(Enum(WatchlistType))
    name = Column(String, index=True)
    aliases = Column(JSON)  # List of aliases
    date_of_birth = Column(Date)
    identifiers = Column(JSON)  # e.g., Passport, National ID
    sanctions = Column(JSON)  # Details of sanctions
