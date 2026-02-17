from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    PLACED = "placed"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    PICKED_UP = "picked_up"
    DELIVERED = "delivered"

class Restaurant(BaseModel):
    id: str
    name: str
    cuisine_types: List[str]
    location: Dict[str, Any]  # GeoJSON
    rating: float
    delivery_radius_km: float
    avg_delivery_min: int
    is_open: bool

class MenuItem(BaseModel):
    id: str
    restaurant_id: str
    name: str
    category: str
    price: float
    description: Optional[str] = None
    allergens: List[str] = []
    is_available: bool
    image_url: Optional[str] = None

class Order(BaseModel):
    id: str
    customer_id: str
    restaurant_id: str
    items: List[MenuItem]
    subtotal: float
    delivery_fee: float
    status: OrderStatus
    placed_at: datetime

class Driver(BaseModel):
    id: str
    name: str
    current_location: Dict[str, Any] # GeoJSON
    is_available: bool
