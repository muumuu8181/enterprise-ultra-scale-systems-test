from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from src.models.optimization_models import (
    ReservationDeal,
    CarbonFootprintSchema,
    TaggingReport,
    ReductionRoadmap
)
from src.services.optimization_service import (
    recommend_reservations,
    calculate_carbon_footprint,
    enforce_tagging_policy,
    check_tagging_compliance,
    purchase_reservation,
    get_reduction_roadmap
)

router = APIRouter(prefix="/optimization", tags=["optimization"])

@router.get("/reserved-instances/recommendations", response_model=List[ReservationDeal])
async def get_reservation_recommendations(account_id: str = Query(..., description="Cloud Account ID")):
    return await recommend_reservations(account_id)

@router.post("/reserved-instances/purchase")
async def purchase_reserved_instance(deal: Dict[str, Any] = Body(...)):
    # In a real app, we would validate 'deal' against a Pydantic model
    return await purchase_reservation(deal)

@router.get("/tagging-compliance/{account_id}", response_model=TaggingReport)
async def get_tagging_compliance(account_id: str):
    return await check_tagging_compliance(account_id)

@router.post("/tagging/enforce", response_model=TaggingReport)
async def enforce_tagging(account_id: str = Body(..., embed=True)):
    return await enforce_tagging_policy(account_id)

@router.post("/carbon/report", response_model=CarbonFootprintSchema)
async def generate_carbon_report(
    account_id: str = Body(..., embed=True),
    period: str = Query("month", description="Report period (e.g. month, year)")
):
    return await calculate_carbon_footprint(account_id, period)

@router.get("/carbon/reduction-roadmap", response_model=ReductionRoadmap)
async def get_carbon_reduction_roadmap():
    return await get_reduction_roadmap()
