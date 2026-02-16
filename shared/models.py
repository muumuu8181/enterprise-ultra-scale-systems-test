from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Product(BaseModel):
    id: str
    name: str
    price: float
    category: str

class SaleItem(BaseModel):
    product_id: str
    quantity: int
    price: float  # Price at the time of sale

class Transaction(BaseModel):
    id: str
    store_id: str
    items: List[SaleItem]
    total: float
    timestamp: datetime
    synced: bool = False
