from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Audio Music Platform"}

def test_discovery_for_you():
    response = client.get("/discovery/for-you")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Mock recommender returns tracks with energy > 0.7
    for track in data:
        assert track["energy"] > 0.7

def test_discovery_new_releases():
    response = client.get("/discovery/new-releases")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_discovery_charts():
    response = client.get("/discovery/charts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_discovery_charts_filter():
    response = client.get("/discovery/charts?genre=pop")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for track in data:
        assert track["genre"] == "pop"

def test_discovery_radio():
    # Use ID '1' which exists in mock data
    response = client.get("/discovery/radio/1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["id"] == "1"

def test_discovery_radio_not_found():
    response = client.get("/discovery/radio/invalid-id")
    assert response.status_code == 404

def test_podcast_details():
    response = client.get("/podcasts/p1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "p1"
    assert data["title"] == "Tech Talk"

def test_podcast_not_found():
    response = client.get("/podcasts/invalid")
    assert response.status_code == 404

def test_podcast_episodes():
    response = client.get("/podcasts/p1/episodes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for episode in data:
        assert episode["podcast_id"] == "p1"

def test_podcast_search():
    response = client.get("/podcasts/search?q=tech")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "Tech" in data[0]["title"]

def test_podcast_subscribe():
    response = client.post("/podcasts/p1/subscribe")
    assert response.status_code == 201

def test_episode_stream():
    response = client.get("/episodes/e1/stream")
    assert response.status_code == 200
    data = response.json()
    assert "stream_url" in data
