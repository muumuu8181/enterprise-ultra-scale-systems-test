from sqlalchemy import select
from src.db.session import AsyncSessionLocal
from src.models.inventory_mes import RawMaterial
from src.schemas.inventory import PurchaseRecommendation, ScheduledOrder
from datetime import date, timedelta

async def run_mrp(forecast_periods: int) -> list[PurchaseRecommendation]:
    """
    Runs Material Requirements Planning.
    Checks for raw materials below reorder point.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(RawMaterial))
        materials = result.scalars().all()
        recommendations = []

        for m in materials:
            # Simple logic: if stock is below reorder point, order enough to cover lead time + safety
            if m.stock_qty < m.reorder_point:
                # Dummy calculation: fill up to reorder_point + buffer based on forecast
                shortage = m.reorder_point - m.stock_qty
                quantity_to_order = shortage + (forecast_periods * 10) # Assume 10 units/period usage

                recommendations.append(PurchaseRecommendation(
                    material_id=m.id,
                    material_name=m.name,
                    quantity_to_order=quantity_to_order,
                    reason=f"Stock {m.stock_qty} below reorder point {m.reorder_point}"
                ))
        return recommendations

async def optimize_production_schedule(orders: list) -> list[ScheduledOrder]:
    """
    Optimizes production schedule.
    Takes a list of ProductionOrder objects (or dicts with id).
    """
    scheduled_orders = []
    current_date = date.today()

    for order in orders:
        # Dummy scheduling logic: one order per day
        # Handle both object and dict access
        order_id = getattr(order, 'id', None) or order.get('id')

        scheduled_orders.append(ScheduledOrder(
            order_id=order_id,
            start_date=current_date,
            status="SCHEDULED"
        ))
        current_date += timedelta(days=1)

    return scheduled_orders

def calculate_oee(availability: float, performance: float, quality: float) -> float:
    """
    Calculates Overall Equipment Effectiveness (OEE).
    OEE = Availability * Performance * Quality
    """
    return availability * performance * quality
