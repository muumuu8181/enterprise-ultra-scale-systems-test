from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from src.models.video_models import Video, VideoStatus
from src.services.video_processor import VideoProcessor
from src.database import get_db

router = APIRouter()
video_processor = VideoProcessor()

class VideoUploadRequest(BaseModel):
    title: str
    description: str
    file_url: str

class VideoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    duration_sec: Optional[int]
    thumbnail_url: Optional[str]
    hls_url: Optional[str]
    views: int
    likes: int
    status: str

    model_config = ConfigDict(from_attributes=True)

@router.post("/videos/upload", response_model=VideoResponse)
def upload_video(request: VideoUploadRequest, db: Session = Depends(get_db)):
    # Check for policy violations
    if video_processor.detect_content_policy_violations(request.title, request.description):
        raise HTTPException(status_code=400, detail="Content policy violation detected.")

    # Create video record
    # Mock creator_id as 1 for now since we don't have auth
    video = Video(
        creator_id=1,
        title=request.title,
        description=request.description,
        status=VideoStatus.PROCESSING.value
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # Mock processing (in a real app, this would be async/background task)
    try:
        # Transcode
        hls_urls = video_processor.transcode_video(request.file_url)
        # Just pick one for simplicity or store all. Model has single hls_url string.
        # Assuming we store the master playlist or one of them.
        video.hls_url = hls_urls.get("1080p") or hls_urls.get("720p")

        # Generate thumbnail
        video.thumbnail_url = video_processor.generate_thumbnail(video.id)

        # Extract subtitles (not stored in Video model based on prompt, maybe just logged or ignored for now)
        subtitles = video_processor.extract_subtitles(video.id)

        video.status = VideoStatus.READY.value
        db.commit()
        db.refresh(video)
    except Exception as e:
        db.rollback()
        video.status = VideoStatus.FAILED.value
        db.commit()
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")

    return video

@router.get("/videos/trending", response_model=List[VideoResponse])
def get_trending_videos(limit: int = 10, db: Session = Depends(get_db)):
    # Simple trending logic: order by views desc
    videos = db.query(Video).filter(Video.status == VideoStatus.READY.value).order_by(desc(Video.views)).limit(limit).all()
    return videos

@router.get("/videos/search", response_model=List[VideoResponse])
def search_videos(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    videos = db.query(Video).filter(
        Video.status == VideoStatus.READY.value,
        or_(
            Video.title.ilike(f"%{q}%"),
            Video.description.ilike(f"%{q}%")
        )
    ).all()
    return videos

@router.get("/videos/{video_id}", response_model=VideoResponse)
def get_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Increment views (simple implementation)
    video.views += 1
    db.commit()
    db.refresh(video)

    return video

@router.post("/videos/{video_id}/like", response_model=VideoResponse)
def like_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video.likes += 1
    db.commit()
    db.refresh(video)

    return video
