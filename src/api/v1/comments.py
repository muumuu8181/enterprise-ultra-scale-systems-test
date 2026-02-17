from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

router = APIRouter()

# In a real application, we would use SQLAlchemy Session and the models from src.models.websocket_collab
# For this implementation, we will use an in-memory list to demonstrate the endpoints.

class CommentCreate(BaseModel):
    user_id: str
    content: str
    anchor_position: Optional[Dict[str, Any]] = None
    thread_id: Optional[str] = None

class CommentResponse(BaseModel):
    id: int
    document_id: str
    user_id: str
    content: str
    resolved: bool
    thread_id: Optional[str] = None
    anchor_position: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# Mock DB
fake_comments_db = []

@router.post("/documents/{id}/comments", response_model=CommentResponse)
async def create_comment(id: str, comment: CommentCreate):
    new_comment = {
        "id": len(fake_comments_db) + 1,
        "document_id": id,
        "user_id": comment.user_id,
        "content": comment.content,
        "resolved": False,
        "thread_id": comment.thread_id,
        "anchor_position": comment.anchor_position
    }
    fake_comments_db.append(new_comment)
    return new_comment

@router.get("/documents/{id}/comments", response_model=List[CommentResponse])
async def get_comments(id: str):
    return [c for c in fake_comments_db if c["document_id"] == id]

@router.put("/comments/{id}/resolve")
async def resolve_comment(id: int):
    for c in fake_comments_db:
        if c["id"] == id:
            c["resolved"] = True
            return {"status": "resolved", "comment": c}
    raise HTTPException(status_code=404, detail="Comment not found")

@router.post("/comments/{id}/reply")
async def reply_comment(id: int, reply: CommentCreate):
    # Verify parent comment exists
    parent = next((c for c in fake_comments_db if c["id"] == id), None)
    if not parent:
         raise HTTPException(status_code=404, detail="Parent comment not found")

    new_reply = {
        "id": len(fake_comments_db) + 1,
        "document_id": parent["document_id"],
        "user_id": reply.user_id,
        "content": reply.content,
        "resolved": False,
        "thread_id": str(id), # Thread ID is the parent comment ID
        "anchor_position": reply.anchor_position
    }
    fake_comments_db.append(new_reply)
    return new_reply
