from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.v1.routing import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_get_directions():
    response = client.post("/routing/directions", json={
        "origin": {"lat": 35.6895, "lon": 139.6917},
        "destination": {"lat": 35.6890, "lon": 139.6910},
        "mode": "walking",
        "avoid": ["highways"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "geometry" in data
    assert data["distance_meters"] > 0
    assert data["mode"] == "walking"

def test_get_isochrone():
    response = client.get("/routing/isochrone?origin=35.6895,139.6917&time_minutes=15")
    assert response.status_code == 200
    data = response.json()
    assert data["geometry"]["type"] == "Polygon"
    assert data["time_minutes"] == 15

def test_get_matrix():
    response = client.post("/routing/matrix", json={
        "origins": [{"lat": 35.6895, "lon": 139.6917}],
        "destinations": [{"lat": 35.6890, "lon": 139.6910}, {"lat": 35.69, "lon": 139.70}]
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["matrix"]) == 1
    assert len(data["matrix"][0]) == 2
