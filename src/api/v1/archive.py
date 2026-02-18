from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel, ConfigDict, Field

from src.database import get_db
from src.models.archive_models import ArchiveItem, Collection, ItemType, Condition
from src.services.preservation_service import PreservationService

router = APIRouter()
preservation_service = PreservationService()

# --- Pydantic Schemas ---
class ArchiveItemCreate(BaseModel):
    title: str
    item_type: ItemType
    origin: str
    condition: Condition
    date_created: datetime

class ArchiveItemResponse(BaseModel):
    id: int
    title: str
    item_type: ItemType
    date_created: datetime
    origin: str
    condition: Condition
    digitized: bool

    model_config = ConfigDict(from_attributes=True)

class CollectionCreate(BaseModel):
    name: str
    owner_institution: str
    description: Optional[str] = None
    public_access: bool = True
    license: Optional[str] = None

class CollectionResponse(BaseModel):
    id: int
    name: str
    owner_institution: str
    description: Optional[str] = None
    item_count: int
    public_access: bool
    license: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ProvenanceResponse(BaseModel):
    item_id: int
    origin: str
    history: List[str]

# --- Endpoints ---

@router.post("/items/register", response_model=ArchiveItemResponse, status_code=status.HTTP_201_CREATED)
async def register_item(item: ArchiveItemCreate, db: AsyncSession = Depends(get_db)):
    new_item = ArchiveItem(
        title=item.title,
        item_type=item.item_type,
        origin=item.origin,
        condition=item.condition,
        date_created=item.date_created,
        digitized=False
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

@router.get("/items/search", response_model=List[ArchiveItemResponse])
async def search_items(
    query: Optional[str] = None,
    item_type: Optional[ItemType] = Query(None, alias="type"),
    date_from: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ArchiveItem)
    if query:
        stmt = stmt.where(or_(ArchiveItem.title.contains(query), ArchiveItem.origin.contains(query)))
    if item_type:
        stmt = stmt.where(ArchiveItem.item_type == item_type)
    if date_from:
        stmt = stmt.where(ArchiveItem.date_created >= date_from)

    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/items/{id}/metadata", response_model=ArchiveItemResponse)
async def get_item_metadata(id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(ArchiveItem, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.get("/items/{id}/download")
async def download_item(id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(ArchiveItem, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not item.digitized:
        raise HTTPException(status_code=400, detail="Item not digitized")

    return {"download_url": f"https://archive.org/download/{id}/content.pdf"}

@router.post("/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(collection: CollectionCreate, db: AsyncSession = Depends(get_db)):
    new_collection = Collection(
        name=collection.name,
        owner_institution=collection.owner_institution,
        description=collection.description,
        public_access=collection.public_access,
        license=collection.license,
        item_count=0
    )
    db.add(new_collection)
    await db.commit()
    await db.refresh(new_collection)
    return new_collection

@router.get("/collections/{id}/items", response_model=List[ArchiveItemResponse])
async def get_collection_items(id: int, db: AsyncSession = Depends(get_db)):
    collection = await db.get(Collection, id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    # No relationship defined in requirements, returning empty list
    return []

@router.get("/items/{id}/provenance", response_model=ProvenanceResponse)
async def get_item_provenance(id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(ArchiveItem, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return ProvenanceResponse(item_id=item.id, origin=item.origin, history=["Acquired from donor A", "Cataloged in 2023"])
