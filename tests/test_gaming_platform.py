from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_start_session():
    response = client.post("/api/v1/sessions/start", json={
        "game_id": "game-123",
        "player_id": "player-456",
        "region": "us-east-1"
    })
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "server_id" in data
    assert data["status"] == "initializing"

def test_get_session_status():
    response = client.get("/api/v1/sessions/123/status")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == 123
    assert data["status"] == "active"

def test_save_game():
    response = client.post("/api/v1/sessions/123/save", json={
        "checkpoint_name": "CheckPoint1",
        "save_data_uri": "s3://bucket/save.dat",
        "playtime_seconds": 3600,
        "checksum": "abc12345"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "save_id" in data

def test_get_stream_url():
    response = client.get("/api/v1/sessions/123/stream-url")
    assert response.status_code == 200
    data = response.json()
    assert "stream_url" in data
    assert "protocol" in data

def test_find_optimal_server():
    response = client.get("/api/v1/servers/find-optimal?game_id=game-1&player_id=player-1")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "region" in data
    assert "status" in data

def test_performance_stats():
    response = client.get("/api/v1/sessions/123/performance-stats")
    assert response.status_code == 200
    data = response.json()
    assert "fps" in data
    assert "latency_ms" in data
