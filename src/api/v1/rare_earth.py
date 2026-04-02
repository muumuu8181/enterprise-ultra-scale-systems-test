from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
import json

from src.core.database import get_db
from src.models.rare_earth_models import MineralDeposit, SupplyContract, ProcessingBatch, Element, MiningStatus, ContractStatus
from src.schemas.rare_earth_schemas import (
    MineralDepositCreate, MineralDepositResponse,
    SupplyContractCreate, SupplyContractResponse,
    ProcessingBatchCreate, ProcessingBatchResponse
)

router = APIRouter()

@router.get("/deposits", response_model=List[MineralDepositResponse])
def list_deposits(
    element: Optional[Element] = None,
    status: Optional[MiningStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(MineralDeposit)
    if element:
        query = query.filter(MineralDeposit.element == element)
    if status:
        query = query.filter(MineralDeposit.mining_status == status)

    # Select the model and the GeoJSON string in one query to avoid N+1
    stmt = query.with_entities(MineralDeposit, func.ST_AsGeoJSON(MineralDeposit.location).label("geojson"))
    results = stmt.all()

    response = []
    for dep, geojson_str in results:
        location = json.loads(geojson_str) if geojson_str else {}
        response.append(MineralDepositResponse(
            id=dep.id,
            element=dep.element,
            location=location,
            estimated_reserves_tonnes=dep.estimated_reserves_tonnes,
            grade_pct=dep.grade_pct,
            mining_status=dep.mining_status,
            operator_id=dep.operator_id
        ))
    return response

@router.get("/deposits/{id}/production-forecast")
def get_production_forecast(id: int, db: Session = Depends(get_db)):
    deposit = db.query(MineralDeposit).filter(MineralDeposit.id == id).first()
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")

    # Mock forecast logic
    return {
        "deposit_id": id,
        "forecast": {
            "2024": deposit.estimated_reserves_tonnes * 0.05,
            "2025": deposit.estimated_reserves_tonnes * 0.06,
        },
        "unit": "tonnes"
    }

@router.get("/contracts", response_model=List[SupplyContractResponse])
def list_contracts(
    element: Optional[Element] = None,
    status: Optional[ContractStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SupplyContract)
    if element:
        query = query.filter(SupplyContract.element == element)
    if status:
        query = query.filter(SupplyContract.status == status)
    return query.all()

@router.post("/contracts/create", response_model=SupplyContractResponse)
def create_contract(contract: SupplyContractCreate, db: Session = Depends(get_db)):
    db_contract = SupplyContract(**contract.model_dump())
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract

@router.get("/batches/{deposit_id}/history", response_model=List[ProcessingBatchResponse])
def get_batch_history(deposit_id: int, db: Session = Depends(get_db)):
    return db.query(ProcessingBatch).filter(ProcessingBatch.deposit_id == deposit_id).all()

@router.post("/batches/log", response_model=ProcessingBatchResponse)
def log_batch(batch: ProcessingBatchCreate, db: Session = Depends(get_db)):
    db_batch = ProcessingBatch(**batch.model_dump())
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

@router.get("/market/spot-prices")
def get_spot_prices():
    return {
        "neodymium": 120.50,
        "dysprosium": 350.00,
        "lanthanum": 5.20,
        "cerium": 4.80,
        "currency": "USD/kg",
        "timestamp": "2023-10-27T10:00:00Z"
    }

@router.get("/analytics/supply-risk-index")
def get_supply_risk_index():
    return {
        "global_risk_score": 7.5,
        "details": {
            "geopolitical": "high",
            "environmental": "medium",
            "logistics": "low"
        }
    }

@router.get("/compliance/export-controls")
def check_export_controls(destination: str = Query(..., min_length=2)):
    restricted = ["North Korea", "Iran", "Syria"]
    if any(r.lower() in destination.lower() for r in restricted):
        return {"allowed": False, "reason": "Embargoed destination"}
    return {"allowed": True, "license_required": False}
