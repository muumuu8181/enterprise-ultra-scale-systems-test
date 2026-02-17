from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_rankings():
    response = client.get("/rankings/top100")
    assert response.status_code == 200
