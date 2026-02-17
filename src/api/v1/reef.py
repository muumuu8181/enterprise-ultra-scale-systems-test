from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker, Session
from celery import Celery
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, field_validator
import os
import json
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from geoalchemy2.elements import WKBElement

# Try to import models, handling path issues if run directly
try:
    from src.models.reef_models import Base, ReefSite, SurveyRecord, BleachingAlert, ReefType, AlertLevel, AlertStatus
except ImportError:
    import sys
    sys.path.append(os.getcwd())
    from src.models.reef_models import Base, ReefSite, SurveyRecord, BleachingAlert, ReefType, AlertLevel, AlertStatus

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/reef_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Celery Setup
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
celery_app = Celery("reef_monitor", broker=CELERY_BROKER_URL)

app = FastAPI(title="Coral Reef Monitoring Platform")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
class ReefSiteResponse(BaseModel):
    id: int
    name: str
    country: str
    reef_type: ReefType
    area_sq_km: Optional[float] = None
    protection_status: Optional[str] = None
    last_survey_date: Optional[datetime] = None
    location: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("location", mode="before")
    @classmethod
    def serialize_location(cls, v):
        # Convert WKBElement to GeoJSON dict
        if isinstance(v, WKBElement):
            return mapping(to_shape(v))
        return v

class SurveySubmit(BaseModel):
    site_id: int
    surveyor_id: str
    coral_cover_pct: float
    bleaching_pct: float
    species_count: int
    water_temp_c: float
    ph_level: float
    visibility_m: float
    photos: Optional[Dict[str, Any]] = None

class SurveyResponse(SurveySubmit):
    id: int
    date: datetime
    model_config = ConfigDict(from_attributes=True)

class AlertResponse(BaseModel):
    id: int
    site_id: int
    alert_level: AlertLevel
    degree_heating_weeks: float
    satellite_sst_c: float
    triggered_at: datetime
    status: AlertStatus
    model_config = ConfigDict(from_attributes=True)

# Endpoints

@app.get("/sites", response_model=List[ReefSiteResponse])
def get_sites(country: Optional[str] = None, protection: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ReefSite)
    if country:
        query = query.filter(ReefSite.country == country)
    if protection:
        query = query.filter(ReefSite.protection_status == protection)
    return query.all()

@app.get("/sites/{id}/health-trend")
def get_health_trend(id: int, db: Session = Depends(get_db)):
    surveys = db.query(SurveyRecord).filter(SurveyRecord.site_id == id).order_by(SurveyRecord.date).all()
    if not surveys:
        return {"site_id": id, "trend": [], "message": "No survey data available"}

    trend = [
        {
            "date": s.date,
            "coral_cover_pct": s.coral_cover_pct,
            "bleaching_pct": s.bleaching_pct
        }
        for s in surveys
    ]
    return {"site_id": id, "trend": trend}

@app.post("/surveys/submit", response_model=SurveyResponse)
def submit_survey(survey: SurveySubmit, db: Session = Depends(get_db)):
    # Check if site exists
    site = db.query(ReefSite).filter(ReefSite.id == survey.site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Reef Site not found")

    db_survey = SurveyRecord(**survey.dict())
    db.add(db_survey)

    # Update last survey date on site
    site.last_survey_date = datetime.utcnow()

    db.commit()
    db.refresh(db_survey)
    return db_survey

@app.get("/surveys/{site_id}/history", response_model=List[SurveyResponse])
def get_survey_history(site_id: int, db: Session = Depends(get_db)):
    return db.query(SurveyRecord).filter(SurveyRecord.site_id == site_id).order_by(SurveyRecord.date.desc()).all()

@app.get("/alerts/active", response_model=List[AlertResponse])
def get_active_alerts(db: Session = Depends(get_db)):
    return db.query(BleachingAlert).filter(BleachingAlert.status == AlertStatus.active).all()

@app.get("/alerts/heatmap")
def get_alerts_heatmap(db: Session = Depends(get_db)):
    alerts = db.query(BleachingAlert).filter(BleachingAlert.status == AlertStatus.active).all()
    result = []
    for alert in alerts:
        result.append({
            "site_id": alert.site_id,
            "alert_level": alert.alert_level,
            "sst": alert.satellite_sst_c
        })
    return {"heatmap_data": result}

@app.get("/species/{site_id}/biodiversity-index")
def get_biodiversity_index(site_id: int, db: Session = Depends(get_db)):
    latest_survey = db.query(SurveyRecord).filter(SurveyRecord.site_id == site_id).order_by(SurveyRecord.date.desc()).first()
    if not latest_survey:
        raise HTTPException(status_code=404, detail="No survey data for site")

    # Mock calculation
    index = latest_survey.species_count * 0.5
    return {"site_id": site_id, "biodiversity_index": index, "species_count": latest_survey.species_count}

@app.get("/analytics/bleaching-forecast")
def get_bleaching_forecast():
    return {
        "forecast_period": "next_4_weeks",
        "risk_level": "high",
        "regions": [
            {"name": "Great Barrier Reef", "probability": 0.85},
            {"name": "Maldives", "probability": 0.70}
        ]
    }
