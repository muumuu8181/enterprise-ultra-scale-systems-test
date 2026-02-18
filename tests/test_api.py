from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.v1.geocoding import router as geocoding_router
from src.api.v1.tiles import router as tiles_router

app = FastAPI()
app.include_router(geocoding_router)
app.include_router(tiles_router)

client = TestClient(app)

def test_geocoding_forward():
    response = client.post("/geocoding/forward", json={"address": "Tokyo Tower"})
    assert response.status_code == 200
    data = response.json()
    assert "lat" in data
    assert "lon" in data
    assert data["address"] == "Tokyo Tower, Minato, Tokyo"

def test_geocoding_reverse():
    response = client.post("/geocoding/reverse", json={"lat": 35.6586, "lon": 139.7454})
    assert response.status_code == 200
    data = response.json()
    assert "Tokyo Tower" in data["address"]

def test_geocoding_search():
    response = client.get("/geocoding/search?q=Tokyo")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == "Tokyo Tower"

def test_tiles():
    response = client.get("/tiles/10/100/100.pbf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-protobuf"
    assert len(response.content) > 0
