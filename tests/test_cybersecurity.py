import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone, timedelta
from src.api.v1.cybersecurity import router as security_router
from src.services.misbehavior_detector import MisbehaviorDetector

# Setup test app
app = FastAPI()
app.include_router(security_router)

@pytest.fixture
def detector():
    return MisbehaviorDetector()

@pytest.mark.asyncio
async def test_report_misbehavior():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "vehicle_id": "malicious_veh_001",
            "evidence": {"log": "suspicious"},
            "reporter_id": "observer_001",
            "attack_type": "spoofing"
        }
        response = await ac.post("/security/misbehavior/report", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reported"
        assert data["trust_impact"] == 20.0 # Spoofing impact

@pytest.mark.asyncio
async def test_get_reports():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/security/misbehavior/reports")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_revoke_vehicle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/security/vehicles/veh_to_revoke/revoke")
        assert response.status_code == 200
        assert response.json()["status"] == "revoked"

@pytest.mark.asyncio
async def test_threat_level():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/security/threat-level")
        assert response.status_code == 200
        assert response.json()["level"] == "LOW"

def test_detector_spoofing(detector):
    # Test impossible speed
    data = {"speed": 400.0}
    assert detector.detect_position_spoofing(data) is True

    # Test normal speed
    data = {"speed": 20.0}
    assert detector.detect_position_spoofing(data) is False

def test_detector_replay(detector):
    now = datetime.now(timezone.utc)

    # Test recent message
    assert detector.detect_replay_attack(now) is False

    # Test old message
    old = now - timedelta(seconds=10)
    assert detector.detect_replay_attack(old) is True

def test_detector_sybil(detector):
    now = datetime.now(timezone.utc).isoformat()

    # Unique reports
    reports = [
        {"latitude": 10.0, "longitude": 10.0, "timestamp": now},
        {"latitude": 20.0, "longitude": 20.0, "timestamp": now}
    ]
    assert detector.detect_sybil_attack(reports) is False

    # Duplicate location reports
    reports_dup = [
        {"latitude": 10.0, "longitude": 10.0, "timestamp": now},
        {"latitude": 10.0, "longitude": 10.0, "timestamp": now}
    ]
    assert detector.detect_sybil_attack(reports_dup) is True

def test_trust_score(detector):
    reports = [
        {"attack_type": "spoofing"}, # -20
        {"attack_type": "replay"}    # -10
    ]
    # Initial 100 -> 100 - 20 - 10 = 70
    score = detector.calculate_trust_score("veh_001", reports)
    assert score == 70.0
