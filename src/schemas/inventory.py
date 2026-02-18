from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import date

class RawMaterialBase(BaseModel):
    name: str
    sku: str
    unit: str
    stock_qty: float = 0.0
    reorder_point: float = 0.0
    lead_days: int = 0

class RawMaterialCreate(RawMaterialBase):
    pass

class RawMaterialResponse(RawMaterialBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class BOMItem(BaseModel):
    material_id: int
    qty_required: float
    waste_factor: float = 0.0

class BOMCreate(BaseModel):
    product_id: int
    items: List[BOMItem]

class ProductionOrderBase(BaseModel):
    product_id: int
    bom_id: int
    planned_qty: float

class ProductionOrderCreate(ProductionOrderBase):
    pass

class ProductionOrderResponse(ProductionOrderBase):
    id: int
    material_reservations: Dict[str, Any]
    status: str
    model_config = ConfigDict(from_attributes=True)

class MaterialStatus(BaseModel):
    is_sufficient: bool
    missing_items: List[Dict[str, Any]]

class PurchaseRecommendation(BaseModel):
    material_id: int
    material_name: str
    quantity_to_order: float
    reason: str

class ScheduledOrder(BaseModel):
    order_id: int
    start_date: date
    status: str

class MaterialIssueRequest(BaseModel):
    pass # Can be empty if just triggering issue
