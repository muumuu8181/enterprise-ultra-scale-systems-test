from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date
from src.models.rare_earth_models import Element, MiningStatus, ContractStatus

class MineralDepositBase(BaseModel):
    element: Element
    location: Dict[str, Any]  # GeoJSON
    estimated_reserves_tonnes: float
    grade_pct: float
    mining_status: MiningStatus = MiningStatus.EXPLORATION
    operator_id: str

class MineralDepositCreate(MineralDepositBase):
    pass

class MineralDepositResponse(MineralDepositBase):
    id: int

    class Config:
        from_attributes = True

class SupplyContractBase(BaseModel):
    buyer_id: str
    seller_id: str
    element: Element
    quantity_kg: float
    price_per_kg: float
    delivery_schedule: Optional[Dict[str, Any]] = None
    incoterm: Optional[str] = None
    status: ContractStatus = ContractStatus.NEGOTIATING

class SupplyContractCreate(SupplyContractBase):
    pass

class SupplyContractResponse(SupplyContractBase):
    id: int

    class Config:
        from_attributes = True

class ProcessingBatchBase(BaseModel):
    deposit_id: int
    input_ore_tonnes: float
    output_elements: Dict[str, float]
    recovery_rate_pct: float
    environmental_compliance: Optional[str] = None
    batch_date: date
    quality_cert_url: Optional[str] = None

class ProcessingBatchCreate(ProcessingBatchBase):
    pass

class ProcessingBatchResponse(ProcessingBatchBase):
    id: int

    class Config:
        from_attributes = True
