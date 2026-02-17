from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union, Any
from pydantic import BaseModel, ConfigDict
from src.db.session import get_db
from src.models.collab_models import Document, DocumentOperation, PresenceInfo, DocType, OpType
from src.services.ot_service import apply_operation, get_document_state
from sqlalchemy import select

router = APIRouter(prefix="/documents", tags=["documents"])

# Pydantic models for request/response
class DocumentCreate(BaseModel):
    title: str
    owner_id: int
    doc_type: DocType

class DocumentResponse(BaseModel):
    id: int
    title: str
    owner_id: int
    doc_type: DocType
    version: int
    collaborators: List[int]

    model_config = ConfigDict(from_attributes=True)

class OperationCreate(BaseModel):
    user_id: int
    op_type: OpType
    position: int
    content: Optional[Any] = None

class OperationResponse(BaseModel):
    id: int
    document_id: int
    user_id: int
    op_type: OpType
    position: int
    content: Optional[Any] = None
    applied: bool

    model_config = ConfigDict(from_attributes=True)

@router.post("/create", response_model=DocumentResponse)
async def create_document(doc: DocumentCreate, db: AsyncSession = Depends(get_db)):
    new_doc = Document(
        title=doc.title,
        owner_id=doc.owner_id,
        doc_type=doc.doc_type,
        collaborators=[doc.owner_id]
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    return new_doc

@router.get("/{id}/snapshot")
async def get_snapshot(id: int, version: int = -1, db: AsyncSession = Depends(get_db)):
    # Version -1 means latest
    content = await get_document_state(id, version, db)
    return {"content": content, "version": version}

@router.post("/{id}/operations", response_model=OperationResponse)
async def apply_op(id: int, op_data: OperationCreate, db: AsyncSession = Depends(get_db)):
    # Convert Pydantic to ORM
    op = DocumentOperation(
        document_id=id,
        user_id=op_data.user_id,
        op_type=op_data.op_type,
        position=op_data.position,
        content=op_data.content,
        applied=False
    )

    # Check document exists
    result = await db.execute(select(Document).where(Document.id == id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Document not found")

    applied_op = await apply_operation(id, op, db)
    return applied_op

@router.get("/{id}/history", response_model=List[OperationResponse])
async def get_history(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(DocumentOperation).where(DocumentOperation.document_id == id).order_by(DocumentOperation.timestamp)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/{id}/share")
async def share_document(id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # We need to create a new list to ensure SQLAlchemy detects change if it's mutable
    current_collabs = list(doc.collaborators) if doc.collaborators else []
    if user_id not in current_collabs:
        current_collabs.append(user_id)
        doc.collaborators = current_collabs
        # We need to flag modified because JSON is sometimes tricky
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(doc, "collaborators")
        await db.commit()

    return {"status": "shared", "collaborators": doc.collaborators}

@router.get("/{id}/collaborators")
async def get_collaborators(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"collaborators": doc.collaborators}
