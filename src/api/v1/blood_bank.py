from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import List, Optional
from datetime import date, timedelta
from src.database import get_db
from src.models.blood_bank_models import (
    Donor, BloodUnit, TransfusionRequest,
    BloodType, BloodComponent, BloodUnitStatus, UrgencyLevel, RequestStatus, CrossmatchStatus
)
from src.schemas.blood_bank_schemas import (
    DonorCreate, DonorResponse,
    BloodUnitCreate, BloodUnitResponse,
    TransfusionRequestCreate, TransfusionRequestResponse,
    InventoryStats, UsageTrend
)

router = APIRouter(prefix="/blood-bank", tags=["Blood Bank"])

# Inventory

@router.get("/inventory", response_model=List[BloodUnitResponse])
async def get_inventory(
    blood_type: Optional[BloodType] = Query(None),
    component: Optional[BloodComponent] = Query(None),
    status: Optional[BloodUnitStatus] = Query(BloodUnitStatus.AVAILABLE),
    db: AsyncSession = Depends(get_db)
):
    query = select(BloodUnit)
    if blood_type:
        query = query.where(BloodUnit.blood_type == blood_type)
    if component:
        query = query.where(BloodUnit.component == component)
    if status:
        query = query.where(BloodUnit.status == status)

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/inventory/critical-levels", response_model=List[str])
async def get_critical_levels(
    threshold: int = Query(5, description="Minimum number of units required"),
    db: AsyncSession = Depends(get_db)
):
    # This is a simplified check. In reality, you'd check per type/component.
    # Group by blood_type and component
    query = select(
        BloodUnit.blood_type,
        BloodUnit.component,
        func.count(BloodUnit.id).label("count")
    ).where(
        BloodUnit.status == BloodUnitStatus.AVAILABLE
    ).group_by(
        BloodUnit.blood_type, BloodUnit.component
    )

    result = await db.execute(query)
    critical = []

    # Initialize counts
    counts = {}
    for bt in BloodType:
        for bc in BloodComponent:
            counts[(bt, bc)] = 0

    for row in result:
        counts[(row.blood_type, row.component)] = row.count

    for (bt, bc), count in counts.items():
        if count < threshold:
            critical.append(f"{bt.value} {bc.value}: {count} units (Critical < {threshold})")

    return critical

# Donors & Donations

@router.post("/donors", response_model=DonorResponse)
async def create_donor(donor: DonorCreate, db: AsyncSession = Depends(get_db)):
    db_donor = Donor(**donor.model_dump())
    db.add(db_donor)
    await db.commit()
    await db.refresh(db_donor)
    return db_donor

@router.post("/donations/register", response_model=BloodUnitResponse)
async def register_donation(donation: BloodUnitCreate, db: AsyncSession = Depends(get_db)):
    # Verify donor exists
    donor = await db.get(Donor, donation.donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")

    # Create blood unit
    db_unit = BloodUnit(**donation.model_dump())

    # Update donor stats
    donor.last_donation_date = donation.collection_date
    donor.total_donations += 1

    db.add(db_unit)
    await db.commit()
    await db.refresh(db_unit)
    return db_unit

@router.get("/donors/{id}/history", response_model=List[BloodUnitResponse])
async def get_donor_history(id: int, db: AsyncSession = Depends(get_db)):
    query = select(BloodUnit).where(BloodUnit.donor_id == id).order_by(desc(BloodUnit.collection_date))
    result = await db.execute(query)
    return result.scalars().all()

# Requests

@router.post("/requests/create", response_model=TransfusionRequestResponse)
async def create_request(request: TransfusionRequestCreate, db: AsyncSession = Depends(get_db)):
    db_request = TransfusionRequest(**request.model_dump())
    db.add(db_request)
    await db.commit()
    await db.refresh(db_request)
    return db_request

@router.post("/requests/{id}/dispatch", response_model=TransfusionRequestResponse)
async def dispatch_request(id: int, db: AsyncSession = Depends(get_db)):
    request = await db.get(TransfusionRequest, id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.status == RequestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Request already completed")

    # Find available units (simplified logic: just check if enough exist, don't link them yet for MVP)
    # Ideally we would reserve specific units.
    # Here we just change status.
    request.status = RequestStatus.DISPATCHED
    await db.commit()
    await db.refresh(request)
    return request

# Compatibility & Analytics

@router.get("/compatibility/crossmatch", response_model=bool)
async def check_crossmatch(
    donor_type: BloodType = Query(alias="donor"),
    patient_type: BloodType = Query(alias="patient"),
    component: BloodComponent = Query(...)
):
    # Simplified compatibility logic
    # Whole Blood / RBC
    compatible = False
    if component in [BloodComponent.WHOLE_BLOOD, BloodComponent.RBC]:
        if donor_type == BloodType.O_NEG:
            compatible = True
        elif donor_type == patient_type:
            compatible = True
        elif patient_type == BloodType.AB_POS:
            compatible = True # Universal recipient
        # Add more rules as needed
    elif component == BloodComponent.PLASMA:
         if donor_type == BloodType.AB_POS: # Universal plasma donor (roughly)
             compatible = True
         elif donor_type == patient_type:
             compatible = True
    else:
        # Default to same type for safety in MVP
        compatible = (donor_type == patient_type)

    return compatible

@router.get("/analytics/usage-trend", response_model=List[UsageTrend])
async def get_usage_trend(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db)
):
    # Count completed/dispatched requests or transfused units
    # Since we don't track timestamp of status change in a separate table in this MVP,
    # we'll just return mock data or count units collected in that period as a proxy for activity.
    # Let's count collected units per day.

    query = select(
        BloodUnit.collection_date,
        func.count(BloodUnit.id).label("count")
    ).where(
        and_(
            BloodUnit.collection_date >= start_date,
            BloodUnit.collection_date <= end_date
        )
    ).group_by(
        BloodUnit.collection_date
    ).order_by(
        BloodUnit.collection_date
    )

    result = await db.execute(query)
    trends = []
    for row in result:
        trends.append(UsageTrend(period=str(row.collection_date), usage_count=row.count))

    return trends

@router.get("/expiring-units", response_model=List[BloodUnitResponse])
async def get_expiring_units(
    days: int = Query(7, description="Days until expiration"),
    db: AsyncSession = Depends(get_db)
):
    target_date = date.today() + timedelta(days=days)
    query = select(BloodUnit).where(
        and_(
            BloodUnit.expiry_date <= target_date,
            BloodUnit.expiry_date >= date.today(),
            BloodUnit.status == BloodUnitStatus.AVAILABLE
        )
    )
    result = await db.execute(query)
    return result.scalars().all()
