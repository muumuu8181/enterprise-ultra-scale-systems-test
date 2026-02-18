import pytest
from httpx import AsyncClient
from src.models.wearable_models import WearableDevice, HealthMetric, DeviceType, MetricType
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_register_device(client: AsyncClient):
    response = await client.post("/devices/register", json={
        "user_id": "user123",
        "device_type": "smartwatch",
        "serial": "SN12345",
        "firmware_version": "1.0.0"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["serial"] == "SN12345"
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_sync_data(client: AsyncClient, db_session):
    # Setup: create device and metric
    device = WearableDevice(
        user_id="user123",
        device_type=DeviceType.smartwatch,
        serial="SN12345",
        firmware_version="1.0.0"
    )
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)

    metric = HealthMetric(
        device_id=device.id,
        metric_type=MetricType.heart_rate,
        value=75.0,
        quality_score=90,
        timestamp=datetime.now(timezone.utc)
    )
    db_session.add(metric)
    await db_session.commit()

    response = await client.get(f"/devices/{device.id}/sync-data")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["value"] == 75.0

@pytest.mark.asyncio
async def test_firmware_update(client: AsyncClient, db_session):
    device = WearableDevice(
        user_id="user123",
        device_type=DeviceType.smartwatch,
        serial="SN12345",
        firmware_version="1.0.0"
    )
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)

    response = await client.post(f"/devices/{device.id}/firmware-update", json={"version": "1.1.0"})
    assert response.status_code == 200
    data = response.json()
    assert data["firmware_version"] == "1.1.0"

@pytest.mark.asyncio
async def test_health_summary(client: AsyncClient, db_session):
    # Setup data
    device = WearableDevice(
        user_id="user123",
        device_type=DeviceType.smartwatch,
        serial="SN12345",
        firmware_version="1.0.0"
    )
    db_session.add(device)
    await db_session.commit()

    response = await client.get("/users/user123/health-summary")
    assert response.status_code == 200
    data = response.json()
    assert "wellness_score" in data
    assert "hrv_report" in data

@pytest.mark.asyncio
async def test_trends(client: AsyncClient, db_session):
    device = WearableDevice(
        user_id="user123",
        device_type=DeviceType.smartwatch,
        serial="SN12345",
        firmware_version="1.0.0"
    )
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)

    metric1 = HealthMetric(
        device_id=device.id,
        metric_type=MetricType.heart_rate,
        value=70.0,
        quality_score=90,
        timestamp=datetime.now(timezone.utc)
    )
    metric2 = HealthMetric(
        device_id=device.id,
        metric_type=MetricType.heart_rate,
        value=72.0,
        quality_score=90,
        timestamp=datetime.now(timezone.utc)
    )
    db_session.add_all([metric1, metric2])
    await db_session.commit()

    response = await client.get("/users/user123/trends?metric=heart_rate")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
