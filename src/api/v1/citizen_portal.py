from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from geoalchemy2.elements import WKTElement

from src.database import get_db
from src.models.citizen_models import CitizenReport, ServiceAppointment
from src.services.report_router import auto_assign_department, notify_citizen

router = APIRouter(prefix="/citizen", tags=["citizen"])

# Pydantic Schemas
class ReportCreate(BaseModel):
    category: str
    description: str
    latitude: float
    longitude: float
    photos: List[str] = []

class ReportResponse(BaseModel):
    id: int
    category: str
    description: str
    status: str
    assigned_dept: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Service(BaseModel):
    id: str
    name: str
    description: str

class AppointmentCreate(BaseModel):
    service_id: str
    citizen_id: str
    scheduled_at: datetime

class AppointmentResponse(BaseModel):
    id: int
    service_id: str
    citizen_id: str
    scheduled_at: datetime
    status: str
    queue_number: int

    model_config = ConfigDict(from_attributes=True)

class Notification(BaseModel):
    id: int
    user_id: str
    message: str
    timestamp: datetime

# Endpoints

@router.post("/reports", response_model=ReportResponse)
async def create_report(report_in: ReportCreate, db: AsyncSession = Depends(get_db)):
    # GeoAlchemy2 POINT format: "POINT(lon lat)"
    # Note: WKT usually expects (x y) -> (lon lat)
    location_wkt = f"POINT({report_in.longitude} {report_in.latitude})"

    new_report = CitizenReport(
        category=report_in.category,
        description=report_in.description,
        location=WKTElement(location_wkt, srid=4326),
        photos=report_in.photos,
        status="Pending"
    )

    # Auto assign department logic
    dept = await auto_assign_department(report_in.category, location=WKTElement(location_wkt, srid=4326))
    new_report.assigned_dept = dept

    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)

    # Notify citizen
    await notify_citizen(new_report.id, "Report received and assigned.")

    return new_report

@router.get("/reports/{report_id}/status", response_model=dict)
async def get_report_status(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CitizenReport).where(CitizenReport.id == report_id))
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {"id": report.id, "status": report.status, "assigned_dept": report.assigned_dept}

@router.get("/services", response_model=List[Service])
async def list_services():
    # Mock data for available services
    return [
        Service(id="residency_cert", name="Residency Certificate", description="Apply for proof of residence"),
        Service(id="tax_payment", name="Tax Payment", description="Pay municipal taxes"),
        Service(id="waste_collection", name="Bulky Waste Collection", description="Schedule pickup for large items")
    ]

@router.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(appt_in: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    # Simple queue number logic (mock: count + 1)
    result = await db.execute(select(ServiceAppointment))
    count = len(result.scalars().all()) # Inefficient for large tables but fine for prototype

    new_appt = ServiceAppointment(
        service_id=appt_in.service_id,
        citizen_id=appt_in.citizen_id,
        scheduled_at=appt_in.scheduled_at,
        queue_number=count + 1,
        status="Scheduled"
    )

    db.add(new_appt)
    await db.commit()
    await db.refresh(new_appt)

    return new_appt

@router.get("/notifications/{user_id}", response_model=List[Notification])
async def get_notifications(user_id: str):
    # Mock notifications
    return [
        Notification(
            id=1,
            user_id=user_id,
            message="Your appointment is confirmed.",
            timestamp=datetime.utcnow()
        ),
        Notification(
            id=2,
            user_id=user_id,
            message="Road damage report #123 is now In Progress.",
            timestamp=datetime.utcnow()
        )
    ]
