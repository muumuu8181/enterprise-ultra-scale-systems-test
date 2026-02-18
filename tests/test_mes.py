import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy import select
from src.models.mes_models import WorkOrder, ProductionLine, QualityCheck, WorkOrderStatus, ProductionLineStatus

@pytest.mark.asyncio
async def test_create_work_order(client: AsyncClient, db_session):
    response = await client.post("/api/v1/production/work-orders", json={
        "product_id": "P001",
        "quantity": 100,
        "scheduled_start": datetime.now(timezone.utc).isoformat()
    })
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == "P001"
    assert data["status"] == "planned"

    # Verify in DB
    result = await db_session.execute(select(WorkOrder).where(WorkOrder.id == data["id"]))
    wo = result.scalar_one()
    assert wo.product_id == "P001"

@pytest.mark.asyncio
async def test_update_status_and_progress(client: AsyncClient, db_session):
    # Create WO
    wo = WorkOrder(
        product_id="P002",
        quantity=200,
        scheduled_start=datetime.now(timezone.utc),
        status=WorkOrderStatus.PLANNED.value
    )
    db_session.add(wo)
    await db_session.commit()
    await db_session.refresh(wo)

    # Update Status
    response = await client.put(f"/api/v1/production/work-orders/{wo.id}/status", json={"status": "running"})
    assert response.status_code == 200
    assert response.json()["status"] == "running"
    assert response.json()["actual_start"] is not None

    # Check Progress
    response = await client.get(f"/api/v1/production/work-orders/{wo.id}/progress")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    # completion is mocked to 50.0 for running
    assert data["completion_percentage"] == 50.0

@pytest.mark.asyncio
async def test_quality_check_and_defect_report(client: AsyncClient, db_session):
    # Create WO
    wo = WorkOrder(
        product_id="P003",
        quantity=50,
        scheduled_start=datetime.now(timezone.utc),
        status=WorkOrderStatus.RUNNING.value,
        actual_start=datetime.now(timezone.utc)
    )
    db_session.add(wo)
    await db_session.commit()
    await db_session.refresh(wo)

    # Add QC (Pass)
    response = await client.post("/api/v1/production/quality-checks", json={
        "work_order_id": wo.id,
        "checkpoint_name": "Visual",
        "result": "pass",
        "measured_value": 10.0,
        "spec_min": 9.0,
        "spec_max": 11.0
    })
    assert response.status_code == 200

    # Add QC (Fail)
    response = await client.post("/api/v1/production/quality-checks", json={
        "work_order_id": wo.id,
        "checkpoint_name": "Dimension",
        "result": "fail",
        "measured_value": 8.5,
        "spec_min": 9.0,
        "spec_max": 11.0
    })
    assert response.status_code == 200

    # Verify defect count in WO
    await db_session.refresh(wo)
    assert wo.defect_count == 1

    # Defect Report
    now = datetime.now(timezone.utc)
    from_date = (now - timedelta(hours=1)).isoformat()
    to_date = (now + timedelta(hours=1)).isoformat()

    response = await client.get("/api/v1/production/quality-checks/defect-report", params={
        "date_from": from_date,
        "date_to": to_date
    })
    assert response.status_code == 200
    data = response.json()
    assert data["total_defects"] == 1
    assert data["details"][0]["checkpoint"] == "Dimension"

@pytest.mark.asyncio
async def test_oee_calculation(client: AsyncClient, db_session):
    # Setup Data
    line = ProductionLine(
        name="Line 1",
        capacity_per_hour=100,
        current_status=ProductionLineStatus.RUNNING.value
    )
    db_session.add(line)
    await db_session.commit()
    await db_session.refresh(line)

    # Create WO that ran for 1 hour
    start_time = datetime.now(timezone.utc) - timedelta(hours=2)
    wo = WorkOrder(
        product_id="P004",
        quantity=100, # 100% performance if run for 1 hour
        scheduled_start=start_time,
        actual_start=start_time,
        status=WorkOrderStatus.COMPLETED.value
    )
    db_session.add(wo)
    await db_session.commit()

    # Get OEE
    # Request range covers the production
    from_date = (start_time - timedelta(minutes=10)).isoformat()
    to_date = (datetime.now(timezone.utc)).isoformat()

    response = await client.get(f"/api/v1/production/production-lines/{line.id}/oee", params={
        "date_from": from_date,
        "date_to": to_date
    })
    assert response.status_code == 200
    data = response.json()

    # Mock Availability is 0.95
    assert data["availability"] == 0.95
    # Quality should be 1.0 (no defects)
    assert data["quality"] == 1.0
    # Performance depends on time range.
    # The range is > 2 hours.
    # Theoretical max for 2 hours = 200.
    # Actual = 100.
    # Performance ~= 0.5.
    assert 0.0 < data["performance"] < 1.0
    assert data["oee"] > 0.0
