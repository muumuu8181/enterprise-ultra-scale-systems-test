from enum import Enum
from sqlalchemy import Column, Integer, String, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel, ConfigDict
from typing import List

Base = declarative_base()

class SampleType(str, Enum):
    blood = "blood"
    saliva = "saliva"
    tissue = "tissue"

class SequencingType(str, Enum):
    WGS = "WGS"
    WES = "WES"
    targeted = "targeted"

class SampleStatus(str, Enum):
    received = "received"
    processing = "processing"
    completed = "completed"

class GenomicSample(Base):
    __tablename__ = "genomic_samples"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    sample_type = Column(SAEnum(SampleType))
    sequencing_type = Column(SAEnum(SequencingType))
    status = Column(SAEnum(SampleStatus), default=SampleStatus.received)

    variants = relationship("Variant", back_populates="sample")

class Variant(Base):
    __tablename__ = "variants"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("genomic_samples.id"))
    chromosome = Column(String)
    position = Column(Integer)
    ref_allele = Column(String)
    alt_allele = Column(String)
    gene = Column(String)
    consequence = Column(String)
    clinvar_significance = Column(String)

    sample = relationship("GenomicSample", back_populates="variants")

# Pydantic Models
class VariantBase(BaseModel):
    chromosome: str
    position: int
    ref_allele: str
    alt_allele: str
    gene: str
    consequence: str
    clinvar_significance: str

    model_config = ConfigDict(from_attributes=True)

class VariantResponse(VariantBase):
    id: int
    sample_id: int

class GenomicSampleCreate(BaseModel):
    patient_id: str
    sample_type: SampleType
    sequencing_type: SequencingType

class GenomicSampleResponse(GenomicSampleCreate):
    id: int
    status: SampleStatus

    model_config = ConfigDict(from_attributes=True)

class GenomicReport(BaseModel):
    sample_id: int
    patient_id: str
    status: SampleStatus
    variants: List[VariantResponse]
    summary: str

    model_config = ConfigDict(from_attributes=True)
