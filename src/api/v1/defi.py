from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from src.services import defi_service
from src.models.defi_monitor import ProtocolType, OracleSource

router = APIRouter()

# Schemas
class RiskDashboardResponse(BaseModel):
    total_tvl: float
    high_risk_protocols: int
    active_alerts: int

class TVLHistoryPoint(BaseModel):
    timestamp: datetime
    tvl_usd: float

class PriceHistoryPoint(BaseModel):
    timestamp: datetime
    price_usd: float

class DeviationAlert(BaseModel):
    oracle_id: int
    token_pair: str
    deviation_pct: float
    timestamp: datetime

class ProtocolCreate(BaseModel):
    name: str
    chain: str
    protocol_type: ProtocolType

class ProtocolResponse(BaseModel):
    id: int
    name: str
    chain: str
    tvl_usd: float
    protocol_type: ProtocolType
    risk_score: float

    class Config:
        from_attributes = True

class AttackResponse(BaseModel):
    id: int
    protocol_id: int
    detected_at: datetime
    attacker_address: str
    profit_usd: float
    attack_type: str
    tx_hash: str

    class Config:
        from_attributes = True

# Endpoints

@router.get("/defi/protocols/risk-dashboard", response_model=RiskDashboardResponse)
async def get_risk_dashboard():
    # Dummy implementation
    return RiskDashboardResponse(
        total_tvl=1000000000.0,
        high_risk_protocols=5,
        active_alerts=2
    )

@router.get("/defi/protocols/{id}/tvl-history", response_model=List[TVLHistoryPoint])
async def get_tvl_history(id: int):
    # Dummy implementation
    return [
        TVLHistoryPoint(timestamp=datetime.now(), tvl_usd=1000000.0)
    ]

@router.get("/oracles/{id}/price-history", response_model=List[PriceHistoryPoint])
async def get_price_history(id: int):
    # Dummy implementation
    return [
        PriceHistoryPoint(timestamp=datetime.now(), price_usd=1500.0)
    ]

@router.get("/oracles/deviation-alerts", response_model=List[DeviationAlert])
async def get_deviation_alerts():
    # Dummy implementation
    return [
        DeviationAlert(
            oracle_id=1,
            token_pair="ETH/USD",
            deviation_pct=5.5,
            timestamp=datetime.now()
        )
    ]

@router.post("/monitor/protocol/add", response_model=ProtocolResponse)
async def add_protocol(protocol: ProtocolCreate):
    # Dummy implementation
    return ProtocolResponse(
        id=1,
        name=protocol.name,
        chain=protocol.chain,
        tvl_usd=0.0,
        protocol_type=protocol.protocol_type,
        risk_score=0.0
    )

@router.get("/attacks/recent", response_model=List[AttackResponse])
async def get_recent_attacks():
    # Call service
    attacks = await defi_service.monitor_flash_loans(1000) # Dummy block number
    # Convert SQLAlchemy models to Pydantic models (handled by response_model)
    # But wait, monitor_flash_loans returns SQLAlchemy objects (or similar).
    # Since I defined them as simple objects in service dummy, it should work if fields match.
    # Actually, in service I returned FlashLoanAttack(id=1, ...).
    # This works if Pydantic can read attributes.
    return attacks
