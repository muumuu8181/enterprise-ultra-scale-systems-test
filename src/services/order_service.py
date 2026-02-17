from datetime import datetime, timezone
from typing import List
import uuid

from src.models.delivery_models import Order, OrderStatus, Driver, MenuItem

async def place_order(customer_id: str, restaurant_id: str, items: List[MenuItem]) -> Order:
    subtotal = sum(item.price for item in items)
    # Mock delivery fee calculation
    delivery_fee = 5.0

    order = Order(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        items=items,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        status=OrderStatus.PLACED,
        placed_at=datetime.now(timezone.utc)
    )
    return order

async def assign_driver(order_id: str) -> Driver:
    # Mock driver assignment
    return Driver(
        id=str(uuid.uuid4()),
        name="John Doe",
        current_location={"type": "Point", "coordinates": [0.0, 0.0]},
        is_available=True
    )

async def calculate_delivery_fee(distance_km: float, surge_multiplier: float = 1.0) -> float:
    base_fee = 2.0
    per_km_fee = 1.0
    return (base_fee + (distance_km * per_km_fee)) * surge_multiplier
