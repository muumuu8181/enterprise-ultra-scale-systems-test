from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import sys
import os

# Ensure src is in path
sys.path.append(os.getcwd())

from src.main import app
from src.database import get_db

client = TestClient(app)

def test_collection_points():
    mock_db = MagicMock()
    mock_point = MagicMock()
    mock_point.id = 1
    mock_point.name = "Test Point"
    mock_point.fill_level_pct = 50.0
    mock_point.point_type = "curbside" # Matches Enum value
    mock_point.next_pickup = None
    # Mock location as a dict so it passes Pydantic validation after to_shape fails
    mock_point.location = {"type": "Point", "coordinates": [139.6917, 35.6895]}
    mock_point.materials_accepted = ["paper", "plastic"]

    # Mocking the query chain
    mock_db.query.return_value.all.return_value = [mock_point]
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_point]

    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/v1/recycling/collection-points")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Point"
    assert data[0]["location"]["type"] == "Point"

    app.dependency_overrides = {}

def test_market_prices():
    mock_db = MagicMock()
    mock_price = MagicMock()
    mock_price.material = "paper"
    mock_price.price_per_kg = 0.5
    mock_price.trend = "up"
    mock_price.effective_date = "2023-10-26T12:00:00"

    mock_db.query.return_value.all.return_value = [mock_price]
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_price]

    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/v1/recycling/market-prices")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["material"] == "paper"

    app.dependency_overrides = {}
