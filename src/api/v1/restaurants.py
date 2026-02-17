from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel

from src.models.delivery_models import Restaurant, MenuItem, Order
from src.services.order_service import place_order

router = APIRouter()

# Mock data
RESTAURANTS: List[Restaurant] = [
    Restaurant(
        id="1",
        name="Pizza Palace",
        cuisine_types=["Italian", "Pizza"],
        location={"type": "Point", "coordinates": [0.0, 0.0]},
        rating=4.5,
        delivery_radius_km=5.0,
        avg_delivery_min=30,
        is_open=True
    )
]

MENUS: Dict[str, List[MenuItem]] = {
    "1": [
        MenuItem(
            id="101",
            restaurant_id="1",
            name="Margherita",
            category="Pizza",
            price=12.0,
            is_available=True
        ),
        MenuItem(
            id="102",
            restaurant_id="1",
            name="Pepperoni",
            category="Pizza",
            price=14.0,
            is_available=True
        )
    ]
}

ORDERS: Dict[str, Order] = {}

class OrderRequest(BaseModel):
    customer_id: str
    restaurant_id: str
    item_ids: List[str]

@router.get("/restaurants/nearby", response_model=List[Restaurant])
async def get_nearby_restaurants(
    lat: float,
    lon: float,
    cuisine: Optional[str] = None
):
    # Mock implementation: return all if no filter or mock filter
    return RESTAURANTS

@router.get("/restaurants/{id}/menu", response_model=List[MenuItem])
async def get_restaurant_menu(id: str):
    if id not in MENUS:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return MENUS[id]

@router.get("/restaurants/{id}/availability")
async def check_restaurant_availability(id: str):
    for r in RESTAURANTS:
        if r.id == id:
            return {"is_open": r.is_open}
    raise HTTPException(status_code=404, detail="Restaurant not found")

@router.post("/orders/place", response_model=Order)
async def place_new_order(request: OrderRequest):
    restaurant_items = MENUS.get(request.restaurant_id, [])
    # Find items by ID
    order_items = []
    for item_id in request.item_ids:
        found = False
        for item in restaurant_items:
            if item.id == item_id:
                order_items.append(item)
                found = True
                break
        if not found:
             raise HTTPException(status_code=400, detail=f"Item {item_id} not found")

    order = await place_order(request.customer_id, request.restaurant_id, order_items)
    ORDERS[order.id] = order
    return order

@router.get("/orders/{id}/track", response_model=Order)
async def track_order(id: str):
    if id not in ORDERS:
        raise HTTPException(status_code=404, detail="Order not found")
    return ORDERS[id]
