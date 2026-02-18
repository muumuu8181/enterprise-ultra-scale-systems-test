from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from src.core.database import get_db
from src.models.social_models import Post, Comment, Like

router = APIRouter()

# Pydantic Models
class PostCreate(BaseModel):
    author_id: int
    content: str
    media_urls: List[str] = []

class PostResponse(BaseModel):
    id: int
    author_id: int
    content: str
    media_urls: List[str]
    likes_count: int
    comments_count: int
    shares_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CommentCreate(BaseModel):
    author_id: int
    content: str
    parent_id: Optional[int] = None

class CommentResponse(BaseModel):
    id: int
    post_id: int
    author_id: int
    content: str
    parent_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LikeRequest(BaseModel):
    user_id: int

# Endpoints

@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    db_post = Post(
        author_id=post.author_id,
        content=post.content,
        media_urls=post.media_urls
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@router.get("/posts/{id}", response_model=PostResponse)
def get_post(id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return None

@router.post("/posts/{id}/like")
def like_post(id: int, like_req: LikeRequest, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing_like = db.query(Like).filter(
        Like.user_id == like_req.user_id,
        Like.target_type == "post",
        Like.target_id == id
    ).first()

    if existing_like:
        return {"message": "Already liked"}

    new_like = Like(user_id=like_req.user_id, target_type="post", target_id=id)
    db.add(new_like)
    post.likes_count = Post.likes_count + 1
    db.commit()
    return {"message": "Liked"}

@router.post("/posts/{id}/share")
def share_post(id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.shares_count = Post.shares_count + 1
    db.commit()
    return {"message": "Shared"}

@router.get("/posts/{id}/comments", response_model=List[CommentResponse])
def get_comments(id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.post_id == id).all()
    return comments

@router.post("/posts/{id}/comments", response_model=CommentResponse)
def create_comment(id: int, comment: CommentCreate, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db_comment = Comment(
        post_id=id,
        author_id=comment.author_id,
        content=comment.content,
        parent_id=comment.parent_id
    )
    db.add(db_comment)
    post.comments_count = Post.comments_count + 1
    db.commit()
    db.refresh(db_comment)
    return db_comment
