import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from src.main import app
from src.database import get_db
from src.models.water_models import TreatmentPlant, PlantStatus, PlantType, WaterQualitySample, SamplePoint, ChemicalDosing, ChemicalType
from datetime import datetime
from shapely.geometry import Point
from geoalchemy2.shape import from_shape

client = TestClient(app)

# Mock DB Session
mock_session = AsyncMock()

async def override_get_db():
    yield mock_session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def mock_db():
    mock_session.reset_mock()
    mock_session.execute = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    return mock_session

def test_get_plants(mock_db):
    # Mock return value
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        TreatmentPlant(
            id=1,
            name="Plant A",
            capacity_mld=100.0,
            plant_type=PlantType.municipal,
            status=PlantStatus.operational
        )
    ]
    mock_db.execute.return_value = mock_result

    response = client.get("/api/v1/water/plants")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Plant A"

def test_get_dashboard(mock_db):
    # Mock plant
    plant = TreatmentPlant(
        id=1,
        name="Plant A",
        capacity_mld=100.0,
        plant_type=PlantType.municipal,
        status=PlantStatus.operational
    )

    mock_plant_result = MagicMock()
    mock_plant_result.scalar_one_or_none.return_value = plant

    mock_quality_result = MagicMock()
    mock_quality_result.scalar_one_or_none.return_value = None

    mock_dosing_result = MagicMock()
    mock_dosing_result.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [mock_plant_result, mock_quality_result, mock_dosing_result]

    response = client.get("/api/v1/water/plants/1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["plant"]["name"] == "Plant A"

def test_get_dashboard_with_location(mock_db):
    # Create a WKBElement using from_shape
    point = Point(1, 1)
    # from_shape returns WKBElement
    location = from_shape(point, srid=4326)

    plant = TreatmentPlant(
        id=1,
        name="Plant A",
        capacity_mld=100.0,
        plant_type=PlantType.municipal,
        status=PlantStatus.operational,
        location=location
    )

    mock_plant_result = MagicMock()
    mock_plant_result.scalar_one_or_none.return_value = plant

    mock_quality_result = MagicMock()
    mock_quality_result.scalar_one_or_none.return_value = None

    mock_dosing_result = MagicMock()
    mock_dosing_result.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [mock_plant_result, mock_quality_result, mock_dosing_result]

    response = client.get("/api/v1/water/plants/1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["plant"]["name"] == "Plant A"
    assert data["plant"]["location"]["type"] == "Point"
    assert data["plant"]["location"]["coordinates"] == [1.0, 1.0]

def test_adjust_dosing(mock_db):
    dosing_data = {
        "plant_id": 1,
        "chemical": "chlorine",
        "dosage_mg_l": 1.5,
        "auto_adjusted": True
    }

    # Mock plant existence check
    mock_plant_result = MagicMock()
    mock_plant_result.scalar_one_or_none.return_value = TreatmentPlant(id=1)
    mock_db.execute.return_value = mock_plant_result

    # We need to simulate refresh setting the ID and timestamp
    async def side_effect_refresh(instance):
        instance.id = 1
        instance.timestamp = datetime.now()

    mock_db.refresh.side_effect = side_effect_refresh

    response = client.post("/api/v1/water/dosing/adjust", json=dosing_data)
    assert response.status_code == 200
    data = response.json()
    assert data["dosage_mg_l"] == 1.5
    assert data["id"] == 1

def test_get_compliance_report(mock_db):
    # Mock samples
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        WaterQualitySample(compliant=True),
        WaterQualitySample(compliant=False),
        WaterQualitySample(compliant=True)
    ]
    mock_db.execute.return_value = mock_result

    response = client.get("/api/v1/water/compliance/report")
    assert response.status_code == 200
    data = response.json()
    assert data["total_samples"] == 3
    assert data["compliant_samples"] == 2
