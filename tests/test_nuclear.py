import pytest
from src.models.nuclear_models import Reactor, ReactorType, ReactorStatus, SensorReading, SensorParameter

@pytest.mark.asyncio
async def test_reactor_dashboard(client, db_session):
    # Setup data
    reactor = Reactor(
        plant_id=1,
        reactor_type=ReactorType.PWR,
        thermal_power_mw=3000.0,
        status=ReactorStatus.OPERATING,
        core_temperature=580.0
    )
    db_session.add(reactor)
    await db_session.commit()
    await db_session.refresh(reactor)

    response = await client.get(f"/api/v1/reactors/{reactor.id}/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == reactor.id
    assert data["status"] == "operating"

@pytest.mark.asyncio
async def test_reactor_shutdown(client, db_session):
    reactor = Reactor(
        plant_id=1,
        reactor_type=ReactorType.PWR,
        thermal_power_mw=3000.0,
        status=ReactorStatus.OPERATING,
        core_temperature=580.0
    )
    db_session.add(reactor)
    await db_session.commit()
    await db_session.refresh(reactor)

    response = await client.post(f"/api/v1/reactors/{reactor.id}/shutdown")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "shutdown"

@pytest.mark.asyncio
async def test_process_sensor_stream(client, db_session):
    # Assuming the service is used correctly by the API
    # I'll create a stream of data
    payload = [
        {
            "reactor_id": 1,
            "sensor_id": "S1",
            "parameter": "temp",
            "value": 1100.0, # Alarm!
            "timestamp": "2023-01-01T00:00:00Z"
        }
    ]
    response = await client.post("/api/v1/sensors/stream", json=payload)
    assert response.status_code == 200
    alarms = response.json()
    assert len(alarms) == 1
    assert alarms[0]["message"] == "Temperature 1100.0 exceeds 1000.0"

@pytest.mark.asyncio
async def test_safety_status(client, db_session):
    reactor = Reactor(
        plant_id=1,
        reactor_type=ReactorType.PWR,
        thermal_power_mw=3000.0,
        status=ReactorStatus.OPERATING,
        core_temperature=1180.0 # Very high!
    )
    db_session.add(reactor)
    await db_session.commit()

    response = await client.get(f"/api/v1/reactors/{reactor.id}/safety-status")
    assert response.status_code == 200
    data = response.json()
    # 1200 - 1180 = 20 margin -> Critical/Warning
    assert data["core_temp_margin"] == 20.0
    assert data["overall_status"] == "CRITICAL" # < 50
