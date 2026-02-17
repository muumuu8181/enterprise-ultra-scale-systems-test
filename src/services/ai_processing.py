from sqlalchemy.ext.asyncio import AsyncSession
from src.models.ocr_models import OCRJob, OCRStatus
from pydantic import BaseModel
from typing import List

class Entity(BaseModel):
    text: str
    label: str
    start: int
    end: int

async def run_ocr(db: AsyncSession, item_id: str, language: str) -> OCRJob:
    job = OCRJob(item_id=item_id, language=language, status=OCRStatus.QUEUED)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job

async def extract_named_entities(text: str) -> List[Entity]:
    # Mock AI extraction
    return [
        Entity(text="MuuMuu8181", label="ORG", start=0, end=10),
        Entity(text="Tokyo", label="GPE", start=15, end=20)
    ]

async def generate_keywords(item_id: str) -> List[str]:
    # Mock keyword generation based on item_id
    return ["archive", "document", "historical", item_id]
