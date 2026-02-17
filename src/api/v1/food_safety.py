from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from src.database import get_db
from src.models.food_safety_models import (
    FoodFacility, Inspection, Violation,
    FacilityType, RiskCategory, FacilityStatus,
    InspectionType, InspectionResult, ViolationSeverity, ViolationArea
)

router = APIRouter(prefix="/food-safety", tags=["Food Safety"])

# --- Pydantic Models ---
class ViolationBase(BaseModel):
    code: str
    description: str
    severity: ViolationSeverity
    area: ViolationArea
    photo_url: Optional[str] = None
    corrected_on_site: bool = False

class ViolationCreate(ViolationBase):
    pass

class ViolationResponse(ViolationBase):
    id: int
    inspection_id: int
    class Config:
        from_attributes = True

class InspectionBase(BaseModel):
    inspector_id: str
    inspection_type: InspectionType
    date: datetime = Field(default_factory=datetime.utcnow)

class InspectionCreate(InspectionBase):
    facility_id: int

class InspectionReport(BaseModel):
    score: int
    violations: List[Dict[str, Any]] # JSON summary
    corrective_actions: List[Dict[str, Any]] # JSON
    result: InspectionResult
    violation_records: List[ViolationCreate] = []

class InspectionResponse(InspectionBase):
    id: int
    facility_id: int
    score: Optional[int] = None
    violations: Optional[List[Dict[str, Any]]] = None
    corrective_actions: Optional[List[Dict[str, Any]]] = None
    result: Optional[InspectionResult] = None
    class Config:
        from_attributes = True

class FoodFacilityBase(BaseModel):
    name: str
    facility_type: FacilityType
    address: str
    license_number: str
    risk_category: RiskCategory
    status: FacilityStatus = FacilityStatus.ACTIVE

class FoodFacilityCreate(FoodFacilityBase):
    pass

class FoodFacilityResponse(FoodFacilityBase):
    id: int
    last_inspection_date: Optional[datetime] = None
    class Config:
        from_attributes = True

class ComplaintCreate(BaseModel):
    facility_id: Optional[int] = None
    description: str
    reporter_contact: Optional[str] = None

# --- Endpoints ---

@router.get("/facilities", response_model=List[FoodFacilityResponse])
async def get_facilities(
    risk: Optional[RiskCategory] = None,
    status: Optional[FacilityStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(FoodFacility)
    if risk:
        query = query.where(FoodFacility.risk_category == risk)
    if status:
        query = query.where(FoodFacility.status == status)

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/facilities/{id}/history", response_model=List[InspectionResponse])
async def get_facility_history(id: int, db: AsyncSession = Depends(get_db)):
    query = select(Inspection).where(Inspection.facility_id == id).order_by(Inspection.date.desc())
    result = await db.execute(query)
    inspections = result.scalars().all()
    # If no inspections, verify facility exists
    if not inspections:
        fac_query = select(FoodFacility).where(FoodFacility.id == id)
        fac_result = await db.execute(fac_query)
        if not fac_result.scalar():
             raise HTTPException(status_code=404, detail="Facility not found")
    return inspections

@router.post("/inspections/schedule", response_model=InspectionResponse)
async def schedule_inspection(inspection: InspectionCreate, db: AsyncSession = Depends(get_db)):
    # Verify facility exists
    fac_query = select(FoodFacility).where(FoodFacility.id == inspection.facility_id)
    fac_result = await db.execute(fac_query)
    if not fac_result.scalar():
        raise HTTPException(status_code=404, detail="Facility not found")

    new_inspection = Inspection(
        facility_id=inspection.facility_id,
        inspector_id=inspection.inspector_id,
        inspection_type=inspection.inspection_type,
        date=inspection.date
    )
    db.add(new_inspection)
    await db.commit()
    await db.refresh(new_inspection)
    return new_inspection

@router.post("/inspections/{id}/submit-report", response_model=InspectionResponse)
async def submit_inspection_report(id: int, report: InspectionReport, db: AsyncSession = Depends(get_db)):
    query = select(Inspection).where(Inspection.id == id)
    result = await db.execute(query)
    inspection = result.scalar()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    inspection.score = report.score
    inspection.violations = report.violations
    inspection.corrective_actions = report.corrective_actions
    inspection.result = report.result

    # Process violation records
    for v in report.violation_records:
        new_violation = Violation(
            inspection_id=id,
            code=v.code,
            description=v.description,
            severity=v.severity,
            area=v.area,
            photo_url=v.photo_url,
            corrected_on_site=v.corrected_on_site
        )
        db.add(new_violation)

    # Update facility last inspection date
    fac_query = select(FoodFacility).where(FoodFacility.id == inspection.facility_id)
    fac_result = await db.execute(fac_query)
    facility = fac_result.scalar()
    if facility:
        facility.last_inspection_date = inspection.date

    await db.commit()
    await db.refresh(inspection)
    return inspection

@router.get("/violations/trending")
async def get_trending_violations(period: str = "month", db: AsyncSession = Depends(get_db)):
    # Mock implementation for trending analysis
    return {"status": "success", "period": period, "trending": [
        {"code": "V001", "count": 15, "description": "Improper food storage"},
        {"code": "V002", "count": 10, "description": "Pest activity"}
    ]}

@router.get("/analytics/compliance-rate")
async def get_compliance_rate(db: AsyncSession = Depends(get_db)):
    # Mock implementation
    return {"compliance_rate": 0.95, "total_inspections": 100, "passed": 95}

@router.post("/complaints/submit")
async def submit_complaint(complaint: ComplaintCreate, db: AsyncSession = Depends(get_db)):
    if complaint.facility_id:
        # Verify facility exists
        fac_query = select(FoodFacility).where(FoodFacility.id == complaint.facility_id)
        fac_result = await db.execute(fac_query)
        if not fac_result.scalar():
            raise HTTPException(status_code=404, detail="Facility not found")

        new_inspection = Inspection(
            facility_id=complaint.facility_id,
            inspector_id="PENDING",
            inspection_type=InspectionType.COMPLAINT,
            date=datetime.utcnow()
        )
        db.add(new_inspection)
        await db.commit()
        await db.refresh(new_inspection)
        return {"message": "Complaint submitted and inspection scheduled", "inspection_id": new_inspection.id}
    return {"message": "Complaint received (no facility linked)"}

@router.get("/public/facility-scores")
async def get_public_scores(zip: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    # Using a simplified query approach
    query = select(FoodFacility)
    if zip:
        query = query.where(FoodFacility.address.contains(zip))

    result = await db.execute(query)
    facilities = result.scalars().all()

    response = []
    for fac in facilities:
        # Get latest completed inspection
        insp_q = select(Inspection).where(
            Inspection.facility_id == fac.id,
            Inspection.result.is_not(None)
        ).order_by(Inspection.date.desc()).limit(1)

        insp_res = await db.execute(insp_q)
        latest = insp_res.scalar()

        if latest and latest.score is not None:
             response.append({
                "facility_name": fac.name,
                "address": fac.address,
                "score": latest.score,
                "grade": "A" if latest.score >= 90 else "B" if latest.score >= 80 else "C"
            })

    return response
