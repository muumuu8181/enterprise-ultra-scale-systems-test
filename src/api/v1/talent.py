from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import cast, String, or_, func
from typing import List, Optional
import datetime
from pydantic import BaseModel, ConfigDict

from src.models.talent_models import TalentProfile, Project, Application, Availability, ProjectStatus, ApplicationStatus, SessionLocal

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models
class TalentProfileBase(BaseModel):
    user_id: int
    skills: List[str]
    experience_years: int
    availability: Availability
    hourly_rate: float
    portfolio_url: Optional[str] = None
    verified: bool = False
    rating: float = 0.0

class TalentProfileCreate(TalentProfileBase):
    pass

class TalentProfileResponse(TalentProfileBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ProjectBase(BaseModel):
    client_id: int
    title: str
    description: str
    required_skills: List[str]
    budget_range: str
    duration_weeks: int
    status: ProjectStatus = ProjectStatus.OPEN

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ApplicationBase(BaseModel):
    talent_id: int
    project_id: int
    cover_letter: str
    proposed_rate: float
    proposed_timeline: str
    status: ApplicationStatus = ApplicationStatus.APPLIED

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationResponse(ApplicationBase):
    id: int
    applied_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# Endpoints

@router.get("/talent/search", response_model=List[TalentProfileResponse])
def search_talent(
    skills: Optional[str] = Query(None, description="Comma separated skills"),
    availability: Optional[Availability] = None,
    db: Session = Depends(get_db)
):
    query = db.query(TalentProfile)
    if availability:
        query = query.filter(TalentProfile.availability == availability)

    # Filtering for skills using string search on JSON array representation
    if skills:
        skill_list = [s.strip() for s in skills.split(",")]
        # Search for any of the skills
        skill_filters = [cast(TalentProfile.skills, String).ilike(f'%"{s}"%') for s in skill_list]
        query = query.filter(or_(*skill_filters))

    return query.all()

@router.get("/talent/{id}/profile", response_model=TalentProfileResponse)
def get_talent_profile(id: int, db: Session = Depends(get_db)):
    talent = db.query(TalentProfile).filter(TalentProfile.id == id).first()
    if not talent:
        raise HTTPException(status_code=404, detail="Talent not found")
    return talent

@router.post("/projects/create", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/projects", response_model=List[ProjectResponse])
def list_projects(
    status: Optional[ProjectStatus] = None,
    skills: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Project)
    if status:
        query = query.filter(Project.status == status)

    if skills:
        skill_list = [s.strip() for s in skills.split(",")]
        # Search for any of the skills
        skill_filters = [cast(Project.required_skills, String).ilike(f'%"{s}"%') for s in skill_list]
        query = query.filter(or_(*skill_filters))
    return query.all()

@router.post("/applications/apply", response_model=ApplicationResponse)
def apply_for_project(application: ApplicationCreate, db: Session = Depends(get_db)):
    db_app = Application(**application.model_dump())
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app

@router.get("/applications/{project_id}/candidates", response_model=List[ApplicationResponse])
def get_project_candidates(project_id: int, db: Session = Depends(get_db)):
    applications = db.query(Application).filter(Application.project_id == project_id).all()
    return applications

@router.post("/applications/{id}/accept", response_model=ApplicationResponse)
def accept_application(id: int, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.status = ApplicationStatus.ACCEPTED
    db.commit()
    db.refresh(app)
    return app

@router.get("/talent/{id}/reviews")
def get_talent_reviews(id: int, db: Session = Depends(get_db)):
    # Mock response
    return [{"id": 1, "talent_id": id, "rating": 5, "comment": "Great work!"}]

@router.get("/analytics/market-rates")
def get_market_rates(skill: str, db: Session = Depends(get_db)):
    # Filter using string search on JSON
    skill_filter = cast(TalentProfile.skills, String).ilike(f'%"{skill}"%')

    # Calculate average rate and count
    result = db.query(
        func.avg(TalentProfile.hourly_rate),
        func.count(TalentProfile.id)
    ).filter(skill_filter).filter(TalentProfile.hourly_rate.isnot(None)).first()

    avg_rate, count = result if result else (0, 0)

    return {"skill": skill, "average_rate": float(avg_rate) if avg_rate else 0, "count": count}
