from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Any
from src.services.dataset_manager import DatasetManager
from src.database import get_db

router = APIRouter(prefix="/datasets", tags=["datasets"])

class DatasetCreate(BaseModel):
    name: str
    storage_path: str
    data_schema: dict = Field(..., alias="schema")
    size_bytes: int
    row_count: int = 0
    tags: Optional[dict] = {}

class DatasetResponse(BaseModel):
    id: int
    name: str
    version: str
    storage_path: str
    schema_: dict = Field(..., alias="schema") # output as schema
    row_count: int
    size_bytes: int
    tags: dict
    created_at: Any

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class SplitRequest(BaseModel):
    train_ratio: float
    val_ratio: float
    test_ratio: float
    random_seed: int = 42

async def get_dataset_manager(db: AsyncSession = Depends(get_db)):
    return DatasetManager(db)

@router.post("/register", response_model=DatasetResponse)
async def register_dataset(dataset: DatasetCreate, manager: DatasetManager = Depends(get_dataset_manager)):
    return await manager.register_dataset(
        name=dataset.name,
        storage_path=dataset.storage_path,
        schema=dataset.data_schema,
        size_bytes=dataset.size_bytes,
        tags=dataset.tags,
        row_count=dataset.row_count
    )

@router.get("/{id}", response_model=DatasetResponse)
async def get_dataset(id: int, manager: DatasetManager = Depends(get_dataset_manager)):
    ds = await manager.get_dataset(id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds

@router.get("/", response_model=List[DatasetResponse])
async def list_datasets(
    search: Optional[str] = None,
    tag_filter: Optional[str] = None,
    manager: DatasetManager = Depends(get_dataset_manager)
):
    # Note: tag_filter implementation is basic in service
    return await manager.list_datasets(search, tag_filter)

@router.post("/{id}/validate")
async def validate_dataset(id: int, manager: DatasetManager = Depends(get_dataset_manager)):
    valid = await manager.validate_schema(id)
    if not valid:
        raise HTTPException(status_code=400, detail="Validation failed or dataset not found")
    return {"valid": valid}

@router.post("/{id}/split")
async def split_dataset(id: int, split_req: SplitRequest, manager: DatasetManager = Depends(get_dataset_manager)):
    try:
        splits = await manager.split_dataset(id, split_req.train_ratio, split_req.val_ratio, split_req.test_ratio, split_req.random_seed)
        return {
            "splits_created": len(splits),
            "details": [{"id": s.id, "type": s.split_type, "count": s.row_count} for s in splits]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
