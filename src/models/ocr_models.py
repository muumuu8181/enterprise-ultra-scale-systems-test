from sqlalchemy import String, Float, Integer, Text, Boolean, DateTime, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
import enum
from datetime import datetime
from typing import Optional

class OCRStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"

class TranscriptionType(str, enum.Enum):
    MANUAL = "manual"
    AI = "ai"
    HYBRID = "hybrid"

class EnrichmentType(str, enum.Enum):
    NER = "ner"
    GEO = "geo"
    DATE = "date"
    TOPIC = "topic"

class OCRJob(Base):
    __tablename__ = "ocr_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    item_id: Mapped[str] = mapped_column(index=True)
    language: Mapped[str]
    status: Mapped[OCRStatus] = mapped_column(default=OCRStatus.QUEUED)
    text_output_uri: Mapped[Optional[str]]
    confidence: Mapped[Optional[float]]
    word_count: Mapped[Optional[int]]

class TranscriptionRecord(Base):
    __tablename__ = "transcription_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    item_id: Mapped[str] = mapped_column(index=True)
    transcriber_id: Mapped[Optional[str]]
    transcription_type: Mapped[TranscriptionType]
    text: Mapped[str] = mapped_column(Text)
    verified: Mapped[bool] = mapped_column(default=False)
    reviewed_at: Mapped[Optional[datetime]]

class MetadataEnrichment(Base):
    __tablename__ = "metadata_enrichments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    item_id: Mapped[str] = mapped_column(index=True)
    enrichment_type: Mapped[EnrichmentType]
    extracted_data: Mapped[dict] = mapped_column(JSON)
    model_version: Mapped[str]
