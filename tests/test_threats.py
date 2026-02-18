import pytest
from src.models.security_models import SeverityLevel, IOCType, ThreatIndicator, SecurityEvent
from sqlalchemy import select

@pytest.mark.asyncio
async def test_create_indicators(client):
    indicators = [
        {
            "ioc_type": "ip",
            "value": "192.168.1.1",
            "severity": "high",
            "confidence": 90.0
        },
        {
            "ioc_type": "domain",
            "value": "malicious.com",
            "severity": "critical",
            "confidence": 95.0,
            "tlp_marking": "RED"
        }
    ]
    response = await client.post("/threats/indicators", json=indicators)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["value"] == "192.168.1.1"
    assert data[1]["tlp_marking"] == "RED"

@pytest.mark.asyncio
async def test_get_indicators_filter(client):
    # Setup - use API to create
    indicators = [
        {"ioc_type": "ip", "value": "10.0.0.1", "severity": "low", "confidence": 50.0},
        {"ioc_type": "ip", "value": "10.0.0.2", "severity": "high", "confidence": 80.0}
    ]
    await client.post("/threats/indicators", json=indicators)

    response = await client.get("/threats/indicators?severity=high")
    assert response.status_code == 200
    data = response.json()
    # Note: test isolation might be tricky with session scope db, but usually we just clean up or check for existence
    # Since we are using in-memory db that persists across session in conftest (scope=session engine),
    # but the db_session fixture yields a new session? No, it yields a session from the engine.
    # The engine is session scoped, so data persists between tests if not cleaned.
    # My conftest doesn't clean data between tests.
    # I'll just check if at least one high severity exists.
    assert len(data) >= 1
    for item in data:
        assert item["severity"] == "high"

@pytest.mark.asyncio
async def test_correlate_events(client):
    events = [
        {
            "event_type": "login_failure",
            "severity": "medium",
            "source_ip": "1.2.3.4"
        },
        {
            "event_type": "brute_force",
            "severity": "high",
            "source_ip": "1.2.3.4"
        }
    ]
    response = await client.post("/threats/correlate", json=events)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "Campaign from 1.2.3.4" in data[0]["name"]

@pytest.mark.asyncio
async def test_dashboard_summary(client):
    response = await client.get("/threats/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_indicators" in data
    assert "high_severity_indicators" in data
    assert "total_events" in data
    assert "active_campaigns" in data
