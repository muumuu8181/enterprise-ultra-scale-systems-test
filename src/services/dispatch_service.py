from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func
from src.models.driver_models import Driver, VehicleType, DriverStatus
from typing import List, Optional, Dict, Any

class DispatchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_nearest_driver(self, restaurant_location: str, vehicle_type: VehicleType) -> Optional[Driver]:
        """
        Finds the nearest available driver to the restaurant location.
        restaurant_location should be a WKT string (e.g., 'POINT(139.6917 35.6895)')
        """
        # Using ST_Distance or <-> operator in PostGIS for nearest neighbor
        # Order by distance and limit 1
        query = select(Driver).where(
            Driver.vehicle_type == vehicle_type,
            Driver.status == DriverStatus.online
        ).order_by(
            func.ST_Distance(Driver.current_location, func.ST_GeomFromText(restaurant_location, 4326))
        ).limit(1)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def optimize_multi_order_route(self, driver_id: int, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Optimizes the route for multiple orders.
        This is a placeholder for a TSP solver.
        """
        # Placeholder logic: just return the orders in the sequence provided
        # In a real system, we would use OSRM or Google Maps API here.
        route_plan = {
            "driver_id": driver_id,
            "orders": orders,
            "optimized_sequence": [order.get("id") for order in orders],
            "total_distance_km": 10.5, # Mock value
            "estimated_duration_min": 45 # Mock value
        }
        return route_plan

    async def calculate_surge_pricing(self, zone_id: str) -> float:
        """
        Calculates surge pricing multiplier based on demand in a zone.
        """
        # Placeholder logic: random or fixed surge based on zone
        # In reality, this would query active orders vs active drivers in the zone (polygon).
        base_surge = 1.0
        # For now, return 1.2 as a mock dynamic value
        return 1.2
