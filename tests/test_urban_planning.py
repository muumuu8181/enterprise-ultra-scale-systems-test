import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.urban_service import UrbanService
from src.models.urban_models import DevelopmentProject
from src.schemas.urban_schemas import DevelopmentProjectCreate, ImpactReport
from src.api.v1.parcels import router, get_service
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
import json

# Test Service
@pytest.mark.asyncio
async def test_calculate_development_impact():
    mock_db = AsyncMock()
    service = UrbanService(mock_db)
    project = DevelopmentProject(id=1, project_type="residential", units=100, floors=5)

    report = await service.calculate_development_impact(project)

    assert report.impact_score > 0
    assert report.project_id == 1

# Test API
app = FastAPI()
app.include_router(router)

from src.db.session import get_db

async def override_get_db():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    yield mock_session

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_impact_analysis_endpoint():
    # Use real service logic but override get_db dependency in app to return mock
    # The default get_db is async generator, dependency overrides can return sync or async

    response = client.post("/zones/impact-analysis", json={
        "parcel_id": "P-123",
        "project_type": "residential",
        "units": 50,
        "floors": 3,
        "status": "proposed"
    })

    assert response.status_code == 200
    data = response.json()
    assert "impact_score" in data
    # 50 * 0.5 + 3 * 1.2 = 25 + 3.6 = 28.6
    assert data["impact_score"] == 28.6

def test_import_parcels():
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]
                    ]
                },
                "properties": {
                    "parcel_id": "P-TEST-1",
                    "zoning_code": "R1",
                    "area_sqm": 100.0,
                    "current_use": "RESIDENTIAL",
                    "allowed_uses": ["RESIDENTIAL"]
                }
            }
        ]
    }

    response = client.post(
        "/parcels/import",
        files={"file": ("parcels.geojson", json.dumps(geojson), "application/json")}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Imported 1 parcels"
