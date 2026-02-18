import pytest
import pytest_asyncio
import math
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from src.models.ml_models import Base, MLModel
from src.models.monitoring_models import ModelAlert
from src.services.drift_detector import DriftDetector
from src.services.model_registry import get_db
from src.api.v1.monitoring import router as monitoring_router

# Test DB Setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    """
    Creates a fresh in-memory database for each test.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()

def test_calculate_psi_logic():
    """Test PSI calculation with known values."""
    detector = DriftDetector(None)

    # Case 1: Identical distributions -> PSI = 0
    dist1 = [0.1] * 10
    assert detector.calculate_psi(dist1, dist1) == 0.0

    # Case 2: Slightly different
    dist2 = [0.11, 0.09] + [0.1] * 8
    psi = detector.calculate_psi(dist1, dist2)
    assert psi > 0.0

    # Case 3: Completely different (but no zeros to avoid exploding)
    # expected: [0.5, 0.5], actual: [0.1, 0.9]
    # (0.1-0.5)*ln(0.1/0.5) + (0.9-0.5)*ln(0.9/0.5)
    # (-0.4)*ln(0.2) + (0.4)*ln(1.8)
    # (-0.4)*(-1.6094) + (0.4)*(0.5877)
    # 0.6437 + 0.2351 = 0.8788
    e = [0.5, 0.5]
    a = [0.1, 0.9]
    psi = detector.calculate_psi(e, a)
    assert math.isclose(psi, 0.8788, rel_tol=0.01)

@pytest.mark.asyncio
async def test_detect_covariate_drift(db_session):
    """Test drift detection (mocked data)."""
    detector = DriftDetector(db_session)

    # Create a dummy model
    model = MLModel(name="TestModel", version="1.0", framework="Test", artifact_uri="uri")
    db_session.add(model)
    await db_session.commit()

    psi, detected = await detector.detect_covariate_drift(model.id)
    # Since data is random, we can't assert exact values easily, but we can check types.
    assert isinstance(psi, float)
    assert isinstance(detected, bool)

@pytest.mark.asyncio
async def test_api_endpoints(db_session):
    """Test API endpoints."""
    app = FastAPI()
    app.include_router(monitoring_router)

    # Override get_db dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create model first
        model = MLModel(name="TestModel", version="1.0", framework="Test", artifact_uri="uri")
        db_session.add(model)
        await db_session.commit()

        # Test GET drift
        response = await ac.get(f"/monitoring/{model.id}/drift")
        assert response.status_code == 200
        data = response.json()
        assert "psi_value" in data
        assert "drift_detected" in data

        # Test POST alert
        alert_data = {"model_id": model.id, "metric": "psi", "threshold": 0.2}
        response = await ac.post("/monitoring/alerts", json=alert_data)
        assert response.status_code == 200
        alert_id = response.json()["id"]

        # Test GET active alerts (none yet triggered)
        response = await ac.get("/monitoring/alerts/active")
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Manually trigger an alert
        stmt = select(ModelAlert).where(ModelAlert.id == alert_id)
        res = await db_session.execute(stmt)
        alert = res.scalars().first()
        alert.triggered_at = datetime.now()
        await db_session.commit()

        response = await ac.get("/monitoring/alerts/active")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == alert_id
