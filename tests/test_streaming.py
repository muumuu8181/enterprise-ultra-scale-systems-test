from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_manifest():
    response = client.get("/videos/123/manifest")
    assert response.status_code == 200
    assert response.json() == {"manifest_url": "https://cdn.example.com/videos/123/manifest.m3u8"}

def test_segment():
    response = client.get("/videos/123/segment/456")
    assert response.status_code == 200
    assert response.json() == {"segment_url": "https://cdn.example.com/videos/123/segments/456.ts"}

def test_watchtime():
    response = client.post("/videos/123/watchtime", json={"position_sec": 10.5, "duration_sec": 120.0})
    assert response.status_code == 200
    assert response.json() == {"status": "success", "position": 10.5}

def test_recommendations():
    response = client.get("/videos/123/recommendations")
    assert response.status_code == 200
    assert response.json() == {"recommendations": ["vid_101", "vid_102", "vid_103"]}

def test_ad_insertion():
    response = client.get("/monetization/ads/123")
    assert response.status_code == 200
    assert response.json() == {"ad_slots": [30, 120, 300]}

def test_revenue():
    response = client.post("/monetization/revenue/creator_abc")
    assert response.status_code == 200
    json_resp = response.json()
    assert "total_views" in json_resp
    assert "ad_revenue" in json_resp
    assert "subscription_revenue" in json_resp
