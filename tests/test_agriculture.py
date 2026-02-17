import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from src.main import app
from src.database import get_db
from src.models.agri_models import Field, SensorNode, CropPrescription
from datetime import date, datetime

client = TestClient(app)

# Mock data
mock_field = Field(
    id=1,
    farm_id="farm1",
    name="Field 1",
    location=MagicMock(), # Mock geometry
    area_hectares=10.5,
    crop_type="corn",
    soil_type="loam",
    irrigation_type="drip",
    planting_date=date(2023, 5, 1),
    expected_harvest=date(2023, 9, 1)
)

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.add = MagicMock()
    return session

@pytest.fixture
def override_get_db(mock_db_session):
    async def _get_db():
        yield mock_db_session
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides = {}

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Smart Agriculture IoT Platform API"}

@patch("src.api.v1.agriculture.wkt_to_geojson")
def test_get_fields(mock_wkt, override_get_db, mock_db_session):
    mock_wkt.return_value = {"type": "Polygon", "coordinates": [[[0,0],[0,1],[1,1],[1,0],[0,0]]]}

    # Mock execute result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_field]
    mock_db_session.execute.return_value = mock_result

    response = client.get("/api/v1/fields")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Field 1"
    assert data[0]["location"] == {"type": "Polygon", "coordinates": [[[0,0],[0,1],[1,1],[1,0],[0,0]]]}

@patch("src.api.v1.agriculture.wkt_to_geojson")
def test_get_sensors(mock_wkt, override_get_db, mock_db_session):
    mock_wkt.return_value = {"type": "Point", "coordinates": [0.5, 0.5]}

    mock_sensor = SensorNode(
        id=1,
        field_id=1,
        sensor_type="soil_moisture",
        location=MagicMock(),
        battery_pct=95.0,
        last_reading_at=datetime.now(),
        status="active"
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_sensor]
    mock_db_session.execute.return_value = mock_result

    response = client.get("/api/v1/sensors/1/live")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["sensor_type"] == "soil_moisture"

def test_health_dashboard(override_get_db):
    response = client.get("/api/v1/fields/1/health-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["health_score"] == 85.5

def test_yield_prediction(override_get_db):
    response = client.get("/api/v1/analytics/yield-prediction?field_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_yield"] == 12000.5

def test_weather_forecast(override_get_db):
    response = client.get("/api/v1/weather/1/7day")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7

def test_create_prescription(override_get_db, mock_db_session):
    payload = {
        "field_id": 1,
        "prescription_type": "fertilizer",
        "product": "Nitrogen",
        "quantity": 100.0,
        "application_method": "spread",
        "scheduled_date": "2023-06-01",
        "status": "planned"
    }

    async def mock_refresh(instance):
        instance.id = 1

    mock_db_session.refresh.side_effect = mock_refresh

    response = client.post("/api/v1/prescriptions/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["product"] == "Nitrogen"
    assert data["id"] == 1
    # Verify db.add was called
    assert mock_db_session.add.called
    assert mock_db_session.commit.called
