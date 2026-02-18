import pytest
from httpx import AsyncClient
from src.models.inventory_mes import RawMaterial, BillOfMaterials, ProductionOrder

@pytest.mark.asyncio
async def test_issue_materials(client: AsyncClient, db_session):
    # Setup
    material = RawMaterial(name="Steel", sku="ST-100", unit="kg", stock_qty=100.0, reorder_point=50.0, lead_days=5)
    db_session.add(material)
    await db_session.commit()
    await db_session.refresh(material)

    bom = BillOfMaterials(product_id=999, material_id=material.id, qty_required=10.0, waste_factor=0.0)
    db_session.add(bom)
    await db_session.commit()

    order = ProductionOrder(product_id=999, bom_id=bom.id, planned_qty=5.0)
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Issue materials
    response = await client.post(f"/api/v1/production-orders/{order.id}/issue-materials")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Check updated stock
    await db_session.refresh(material)
    # Required: 10 * 5 = 50. Stock was 100. New stock = 50.
    assert material.stock_qty == 50.0

    # Check order status
    await db_session.refresh(order)
    assert order.status == "ISSUED"
