from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from src.database import get_db
from src.services.ai_processing import run_ocr, extract_named_entities, generate_keywords
from src.models.ocr_models import OCRJob, OCRStatus, TranscriptionRecord, MetadataEnrichment, TranscriptionType, EnrichmentType

router = APIRouter()

# Pydantic Schemas

class OCRRequest(BaseModel):
    language: str

class OCRJobResponse(BaseModel):
    id: int
    item_id: str
    language: str
    status: OCRStatus
    text_output_uri: Optional[str] = None
    confidence: Optional[float] = None
    word_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class TranscriptionRequest(BaseModel):
    transcription_type: TranscriptionType
    text: str
    transcriber_id: Optional[str] = None

class TranscriptionResponse(BaseModel):
    id: int
    item_id: str
    transcription_type: TranscriptionType
    text: str
    verified: bool

    model_config = ConfigDict(from_attributes=True)

class EnrichmentResponse(BaseModel):
    id: int
    item_id: str
    enrichment_type: EnrichmentType
    extracted_data: Dict[str, Any]
    model_version: str

    model_config = ConfigDict(from_attributes=True)

class BatchEnrichRequest(BaseModel):
    item_ids: List[str]

# API Endpoints

@router.post("/items/{item_id}/ocr-request", response_model=OCRJobResponse)
async def create_ocr_request(item_id: str, request: OCRRequest, db: AsyncSession = Depends(get_db)):
    """
    Initiates an OCR job for a specific item.
    """
    job = await run_ocr(db, item_id=item_id, language=request.language)
    return job

@router.get("/ocr-jobs/{job_id}/result", response_model=OCRJobResponse)
async def get_ocr_result(job_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the result of an OCR job.
    """
    stmt = select(OCRJob).where(OCRJob.id == job_id)
    result = await db.execute(stmt)
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="OCR Job not found")
    return job

@router.post("/items/{item_id}/transcription", response_model=TranscriptionResponse)
async def create_transcription(item_id: str, request: TranscriptionRequest, db: AsyncSession = Depends(get_db)):
    """
    Submits a transcription for an item.
    """
    transcription = TranscriptionRecord(
        item_id=item_id,
        transcriber_id=request.transcriber_id,
        transcription_type=request.transcription_type,
        text=request.text,
        verified=False
    )
    db.add(transcription)
    await db.commit()
    await db.refresh(transcription)
    return transcription

@router.get("/items/{item_id}/enrichments", response_model=List[EnrichmentResponse])
async def get_enrichments(item_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves metadata enrichments for an item.
    """
    stmt = select(MetadataEnrichment).where(MetadataEnrichment.item_id == item_id)
    result = await db.execute(stmt)
    enrichments = result.scalars().all()
    return list(enrichments)

@router.post("/items/batch-enrich")
async def batch_enrich(request: BatchEnrichRequest, db: AsyncSession = Depends(get_db)):
    """
    Triggers AI metadata extraction for a batch of items.
    """
    processed_items = []
    for item_id in request.item_ids:
        # Mock logic: Generate keywords and entities
        keywords = await generate_keywords(item_id)

        # We can pretend we have some text to analyze, or use a placeholder
        entities = await extract_named_entities("Sample text for extraction")

        # Save keyword enrichment
        enrichment_kw = MetadataEnrichment(
            item_id=item_id,
            enrichment_type=EnrichmentType.TOPIC,
            extracted_data={"keywords": keywords},
            model_version="keyword-v1"
        )
        db.add(enrichment_kw)

        # Save NER enrichment
        enrichment_ner = MetadataEnrichment(
            item_id=item_id,
            enrichment_type=EnrichmentType.NER,
            extracted_data={"entities": [e.model_dump() for e in entities]},
            model_version="ner-v1"
        )
        db.add(enrichment_ner)

        processed_items.append(item_id)

    await db.commit()
    return {"message": "Batch enrichment processed", "processed_items": processed_items}
