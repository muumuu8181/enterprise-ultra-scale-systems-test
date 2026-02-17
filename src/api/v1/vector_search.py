from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.vector_store import VectorStore

router = APIRouter()


class CreateCollectionRequest(BaseModel):
    name: str
    dimension: int
    metric: str = "cosine"


class UpsertVectorRequest(BaseModel):
    collection: str
    id: str
    vector: List[float]
    metadata: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    collection: str
    query_vector: List[float]
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None


class CollectionResponse(BaseModel):
    id: int
    name: str
    dimension: int
    metric: str
    item_count: int
    created_at: Any

    model_config = ConfigDict(from_attributes=True)


class VectorItemResponse(BaseModel):
    id: int
    collection_id: int
    external_id: str
    metadata: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


@router.post(
    "/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED
)
async def create_collection(
    request: CreateCollectionRequest, db: AsyncSession = Depends(get_db)
):
    store = VectorStore(db)
    try:
        collection = await store.create_collection(
            request.name, request.dimension, request.metric
        )
        return collection
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/index", status_code=status.HTTP_200_OK)
async def index_vector(
    request: UpsertVectorRequest, db: AsyncSession = Depends(get_db)
):
    store = VectorStore(db)
    try:
        await store.upsert_vector(
            request.collection, request.id, request.vector, request.metadata
        )
        return {"status": "success", "id": request.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search", response_model=List[VectorItemResponse])
async def search_vectors(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    store = VectorStore(db)
    try:
        results = await store.search_nearest(
            request.collection, request.query_vector, request.top_k, request.filters
        )
        return [
            VectorItemResponse(
                id=item.id,
                collection_id=item.collection_id,
                external_id=item.external_id,
                metadata=item.metadata_,
            )
            for item in results
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{collection}/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vector(collection: str, id: str, db: AsyncSession = Depends(get_db)):
    store = VectorStore(db)
    try:
        await store.delete_vector(collection, id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
