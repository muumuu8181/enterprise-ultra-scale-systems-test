import pytest
from unittest.mock import patch, MagicMock
from src.services.mrp_service import calculate_oee, run_mrp
from src.models.inventory_mes import RawMaterial

def test_oee_calculation():
    # OEE = Availability * Performance * Quality
    # Example: 0.9 * 0.95 * 0.99 = 0.84645
    availability = 0.9
    performance = 0.95
    quality = 0.99
    expected = 0.9 * 0.95 * 0.99

    result = calculate_oee(availability, performance, quality)
    assert abs(result - expected) < 1e-9

@pytest.mark.asyncio
async def test_mrp_run(db_session):
    # Setup data
    material = RawMaterial(
        name="Steel",
        sku="ST-001",
        unit="kg",
        stock_qty=50.0,
        reorder_point=100.0,
        lead_days=5
    )
    db_session.add(material)
    await db_session.commit()
    await db_session.refresh(material)

    # Mock AsyncSessionLocal to return db_session
    class MockSessionContext:
        async def __aenter__(self):
            return db_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # We patch the call to AsyncSessionLocal in src.services.mrp_service
    # Since run_mrp calls AsyncSessionLocal(), we patch the class/factory itself.
    with patch("src.services.mrp_service.AsyncSessionLocal", return_value=MockSessionContext()):
        recommendations = await run_mrp(forecast_periods=3)

    assert len(recommendations) == 1
    rec = recommendations[0]
    assert rec.material_id == material.id
    # Logic in mrp_service: shortage + forecast * 10
    # shortage = 100 - 50 = 50
    # forecast * 10 = 30
    # total = 80
    assert rec.quantity_to_order == 80.0
    assert rec.reason == f"Stock {material.stock_qty} below reorder point {material.reorder_point}"
