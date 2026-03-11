import sys
import os
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime, timezone

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mocking sqlalchemy imports if needed, but since we are just checking instantiation, it should be fine if dependencies are installed.
try:
    from api.v1.census import router
    from models.census_models import CensusRound, Household, Demographic, CensusStatus, DwellingType
except ImportError as e:
    print(f"Import Error: {e}")
    # If imports fail due to missing packages in this environment, we might need to skip or mock
    # But let's assume standard packages are available or I can't run tests anyway.
    raise

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_models():
    # Test CensusRound instantiation (not database persistence)
    round = CensusRound(
        year=2023,
        country="Testland",
        status=CensusStatus.planning
    )
    assert round.year == 2023
    assert round.status == CensusStatus.planning

    # Test Household
    household = Household(
        census_round_id=1,
        district_id=101,
        address_hash="abc",
        dwelling_type=DwellingType.house,
        completed_at=datetime.now(timezone.utc)
    )
    assert household.dwelling_type == DwellingType.house

    # Test Demographic
    demographic = Demographic(
        household_id=1,
        age=30,
        gender="M",
        disability={"vision": "none"}
    )
    assert demographic.age == 30
    assert demographic.disability["vision"] == "none"

def test_api_endpoints():
    # GET /rounds
    response = client.get("/census/rounds?country=Testland&year=2023")
    assert response.status_code == 200
    assert response.json()["filters"]["country"] == "Testland"

    # GET /rounds/{id}/progress
    response = client.get("/census/rounds/1/progress")
    assert response.status_code == 200
    assert response.json()["progress"] == "50%"

    # GET /demographics/summary
    response = client.get("/census/demographics/summary?district=D1")
    assert response.status_code == 200
    assert response.json()["filters"]["district"] == "D1"

    # GET /demographics/pyramid/{district}
    response = client.get("/census/demographics/pyramid/D1")
    assert response.status_code == 200
    assert response.json()["district"] == "D1"

    # GET /districts/{id}/population
    response = client.get("/census/districts/100/population")
    assert response.status_code == 200
    assert response.json()["population"] == 10000

    # GET /comparison
    response = client.get("/census/comparison?metric=growth")
    assert response.status_code == 200
    assert response.json()["metric"] == "growth"

    # GET /analytics/growth-trend
    response = client.get("/census/analytics/growth-trend?region=North")
    assert response.status_code == 200
    assert response.json()["region"] == "North"

    # GET /data/download
    response = client.get("/census/data/download?format=csv")
    assert response.status_code == 200
    assert response.json()["format"] == "csv"

    # GET /mapping/choropleth
    response = client.get("/census/mapping/choropleth?metric=density")
    assert response.status_code == 200
    assert response.json()["metric"] == "density"

if __name__ == "__main__":
    # Manually run tests if pytest is not available or to debug
    try:
        test_models()
        test_api_endpoints()
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
