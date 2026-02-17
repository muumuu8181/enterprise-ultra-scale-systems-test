from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict
from src.models.classroom_models import VirtualClass, Enrollment, LiveSession, SessionConfig, Certificate, ClassStatus
from src.services import classroom_service

router = APIRouter()

# Placeholder for DB dependency.
# This will be overridden in tests or provided by main app.
async def get_db():
    raise NotImplementedError("Database dependency not implemented")

# Request/Response Schemas
class CreateClassRequest(BaseModel):
    instructor_id: str
    title: str
    subject: str
    schedule: Dict[str, Any]
    max_students: int

class EnrollRequest(BaseModel):
    student_id: str

class VirtualClassResponse(BaseModel):
    id: int
    instructor_id: str
    title: str
    subject: str
    schedule: Dict[str, Any]
    max_students: int
    status: ClassStatus

    model_config = ConfigDict(from_attributes=True)

class EnrollmentResponse(BaseModel):
    id: int
    class_id: int
    student_id: str
    status: str = "enrolled"

    model_config = ConfigDict(from_attributes=True)

@router.post("/classes/create", response_model=VirtualClassResponse)
async def create_class(request: CreateClassRequest, db: AsyncSession = Depends(get_db)):
    new_class = VirtualClass(
        instructor_id=request.instructor_id,
        title=request.title,
        subject=request.subject,
        schedule=request.schedule,
        max_students=request.max_students
    )
    db.add(new_class)
    await db.commit()
    await db.refresh(new_class)
    return new_class

@router.get("/classes/catalog", response_model=List[VirtualClassResponse])
async def get_catalog(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VirtualClass))
    return result.scalars().all()

@router.post("/classes/{class_id}/enroll", response_model=EnrollmentResponse)
async def enroll_student(class_id: int, request: EnrollRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VirtualClass).where(VirtualClass.id == class_id))
    virtual_class = result.scalars().first()
    if not virtual_class:
        raise HTTPException(status_code=404, detail="Class not found")

    enrollment = Enrollment(
        class_id=class_id,
        student_id=request.student_id
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment

@router.get("/classes/{class_id}/schedule")
async def get_schedule(class_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VirtualClass).where(VirtualClass.id == class_id))
    virtual_class = result.scalars().first()
    if not virtual_class:
        raise HTTPException(status_code=404, detail="Class not found")
    return virtual_class.schedule

@router.get("/classes/{class_id}/live-stream-url")
async def get_live_stream_url(class_id: int, db: AsyncSession = Depends(get_db)):
    # Get active session
    result = await db.execute(select(LiveSession).where(LiveSession.class_id == class_id).order_by(LiveSession.started_at.desc()))
    session = result.scalars().first()
    if not session:
        # If no session, maybe we can't get URL
        raise HTTPException(status_code=404, detail="No active session found")

    return {"url": f"rtmp://stream.classroom.com/{session.id}"}

@router.post("/classes/{class_id}/start-session", response_model=SessionConfig)
async def start_session(class_id: int, db: AsyncSession = Depends(get_db)):
    try:
        config = await classroom_service.start_live_session(class_id, db)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
