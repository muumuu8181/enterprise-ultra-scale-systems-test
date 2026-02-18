import sys
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.v1.content import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_get_edge_nodes_health():
    response = client.get("/cdn/edge-nodes/health")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "location" in data[0]

def test_ingest_content():
    files = {'file': ('test.mp4', b'video content', 'video/mp4')}
    response = client.post("/content/ingest", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "resolutions" in data
    assert "adaptive" in data["resolutions"]

def test_get_manifest():
    # First ingest to get an ID
    files = {'file': ('test.mp4', b'video content', 'video/mp4')}
    ingest_response = client.post("/content/ingest", files=files)
    content_id = ingest_response.json()["id"]

    response = client.get(f"/content/{content_id}/manifest")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.apple.mpegurl"
    assert "#EXTM3U" in response.text

def test_create_cache_rule():
    rule = {
        "id": "rule-1",
        "content_type": "video/mp4",
        "ttl_seconds": 3600,
        "priority": 1,
        "edge_nodes": ["node-1"]
    }
    response = client.post("/cdn/cache-rules", json=rule)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "rule-1"

def test_purge_cache():
    response = client.post("/content/some-id/purge-cache")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
