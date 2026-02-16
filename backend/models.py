from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class LotStatus(str, Enum):
    WAITING = "WAITING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    HOLD = "HOLD"

class EquipmentStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    DOWN = "DOWN"
    MAINTENANCE = "MAINTENANCE"

class RecipeParameter(BaseModel):
    name: str
    target: float
    unit: str
    tolerance_upper: float
    tolerance_lower: float

class Recipe(BaseModel):
    recipe_id: str
    description: str
    parameters: List[RecipeParameter]

class Lot(BaseModel):
    lot_id: str
    product_id: str
    quantity: int
    current_step: Optional[str] = None
    status: LotStatus = LotStatus.WAITING
    history: List[str] = []

class Equipment(BaseModel):
    equipment_id: str
    type: str  # e.g., 'ETCH', 'CVD', 'LITHO'
    status: EquipmentStatus = EquipmentStatus.IDLE
    current_lot_id: Optional[str] = None
    last_maintenance: Optional[str] = None
