from enum import Enum
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass

class CensusStatus(str, Enum):
    planning = "planning"
    enumeration = "enumeration"
    processing = "processing"
    published = "published"

class DwellingType(str, Enum):
    house = "house"
    apartment = "apartment"
    mobile = "mobile"
    other = "other"

class CensusRound(Base):
    __tablename__ = "census_rounds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[CensusStatus] = mapped_column(SQLEnum(CensusStatus), default=CensusStatus.planning)
    coverage_pct: Mapped[float] = mapped_column(Float, default=0.0)
    total_population: Mapped[int] = mapped_column(Integer, default=0)
    households_enumerated: Mapped[int] = mapped_column(Integer, default=0)

    households: Mapped[List["Household"]] = relationship("Household", back_populates="census_round")


class Household(Base):
    __tablename__ = "households"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    census_round_id: Mapped[int] = mapped_column(ForeignKey("census_rounds.id"), nullable=False)
    district_id: Mapped[int] = mapped_column(Integer, nullable=False)
    address_hash: Mapped[str] = mapped_column(String, nullable=False)
    dwelling_type: Mapped[DwellingType] = mapped_column(SQLEnum(DwellingType), default=DwellingType.house)
    rooms: Mapped[int] = mapped_column(Integer, default=1)
    members_count: Mapped[int] = mapped_column(Integer, default=1)
    income_bracket: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    census_round: Mapped["CensusRound"] = relationship("CensusRound", back_populates="households")
    demographics: Mapped[List["Demographic"]] = relationship("Demographic", back_populates="household")


class Demographic(Base):
    __tablename__ = "demographics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String, nullable=False)
    ethnicity: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    education_level: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    employment_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    language_primary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    disability: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    household: Mapped["Household"] = relationship("Household", back_populates="demographics")
