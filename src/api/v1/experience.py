from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from src.database import get_db
from src.services.experience_service import ExperienceService
from src.schemas.experience_schemas import (
    EmployeeResponse, SurveyResponseCreate, SurveyResponseResponse,
    ExperienceScoreResponse, JourneyEvent, TrendResponse, AttritionRiskResponse,
    KudosCreate
)

router = APIRouter(prefix="", tags=["experience"]) # Prefix handled in main.py usually, or here. User asked for specific paths like /employees/{id}/...

# Dependency Injection for Service
async def get_service(db: AsyncSession = Depends(get_db)) -> ExperienceService:
    return ExperienceService(db)

@router.get("/employees/{id}/experience-score", response_model=ExperienceScoreResponse)
async def get_experience_score(id: int, service: ExperienceService = Depends(get_service)):
    result = await service.get_employee_experience_score(id)
    if not result:
        raise HTTPException(status_code=404, detail="Employee not found")
    return result

@router.get("/employees/{id}/journey", response_model=List[JourneyEvent])
async def get_journey(id: int, service: ExperienceService = Depends(get_service)):
    result = await service.get_employee_journey(id)
    return result

@router.post("/surveys/submit", response_model=SurveyResponseResponse)
async def submit_survey(survey: SurveyResponseCreate, service: ExperienceService = Depends(get_service)):
    return await service.submit_survey(survey.model_dump())

@router.get("/surveys/results", response_model=List[SurveyResponseResponse])
async def get_surveys(type: Optional[str] = None, period: Optional[str] = None, service: ExperienceService = Depends(get_service)):
    return await service.get_survey_results(type, period)

@router.get("/wellbeing/team/{department}/summary")
async def get_team_wellbeing(department: str, service: ExperienceService = Depends(get_service)):
    return await service.get_team_wellbeing_summary(department)

@router.get("/wellbeing/trends", response_model=TrendResponse)
async def get_trends(service: ExperienceService = Depends(get_service)):
    return await service.get_wellbeing_trends()

@router.get("/analytics/engagement-drivers")
async def get_drivers(service: ExperienceService = Depends(get_service)):
    return await service.get_engagement_drivers()

@router.get("/analytics/attrition-risk", response_model=List[AttritionRiskResponse])
async def get_attrition(service: ExperienceService = Depends(get_service)):
    return await service.get_attrition_risk()

@router.post("/recognition/kudos")
async def submit_kudos(kudos: KudosCreate, service: ExperienceService = Depends(get_service)):
    return await service.submit_kudos(kudos.model_dump())
