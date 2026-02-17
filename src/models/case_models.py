from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy.types import JSON
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict

Base = declarative_base()

class LegalCase(Base):
    __tablename__ = "legal_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    case_type: Mapped[str] = mapped_column(String)  # civil/criminal/arbitration
    parties: Mapped[Any] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String)
    jurisdiction: Mapped[str] = mapped_column(String)
    assigned_attorney_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    milestones: Mapped[List["CaseMilestone"]] = relationship("CaseMilestone", back_populates="case")
    research_queries: Mapped[List["ResearchQuery"]] = relationship("ResearchQuery", back_populates="case")

class CaseMilestone(Base):
    __tablename__ = "case_milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("legal_cases.id"))
    milestone_type: Mapped[str] = mapped_column(String) # filing/hearing/judgment
    scheduled_date: Mapped[datetime] = mapped_column(DateTime)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    case: Mapped["LegalCase"] = relationship("LegalCase", back_populates="milestones")

class ResearchQuery(Base):
    __tablename__ = "research_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("legal_cases.id"))
    query: Mapped[str] = mapped_column(Text)
    citations_found: Mapped[Any] = mapped_column(JSON)
    relevance_scores: Mapped[Any] = mapped_column(JSON)

    case: Mapped["LegalCase"] = relationship("LegalCase", back_populates="research_queries")

# Pydantic Schemas

class CaseBase(BaseModel):
    case_number: str
    case_type: str
    parties: Any
    status: str
    jurisdiction: str
    assigned_attorney_id: Optional[int] = None

class CaseCreate(CaseBase):
    pass

class CaseResponse(CaseBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class MilestoneBase(BaseModel):
    milestone_type: str
    scheduled_date: datetime
    completed: bool = False
    notes: Optional[str] = None

class MilestoneCreate(MilestoneBase):
    pass

class MilestoneResponse(MilestoneBase):
    id: int
    case_id: int
    model_config = ConfigDict(from_attributes=True)

class ResearchQueryBase(BaseModel):
    query: str
    citations_found: Any
    relevance_scores: Any

class ResearchQueryCreate(ResearchQueryBase):
    pass

class ResearchQueryResponse(ResearchQueryBase):
    id: int
    case_id: int
    model_config = ConfigDict(from_attributes=True)
