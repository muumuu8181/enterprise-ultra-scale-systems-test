import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.v1.features import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_create_feature_group():
    response = client.post("/feature-groups", json={
        "name": "user_basic",
        "entity_type": "user",
        "storage_type": "online",
        "description": "Basic user features"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "user_basic"
    assert "id" in data

def test_get_features_in_group():
    # First create a group
    g_resp = client.post("/feature-groups", json={
        "name": "user_advanced",
        "entity_type": "user",
        "storage_type": "both"
    })
    group_id = g_resp.json()["id"]

    # Create a feature
    client.post("/features/register", json={
        "group_id": group_id,
        "name": "age",
        "dtype": "int"
    })

    response = client.get(f"/feature-groups/{group_id}/features")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    names = [f["name"] for f in data]
    assert "age" in names

def test_get_feature_statistics():
    # Feature ID 1 doesn't need to exist in mock service logic (it just uses the ID)
    response = client.get("/features/1/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "drift_detected" in data
    assert "drift_score" in data

def test_materialize_feature_view():
    # Create a view first
    view_response = client.post("/feature-views", json={
        "features": ["age", "income"],
        "source_query": "SELECT * FROM users",
        "freshness_minutes": 60
    })
    assert view_response.status_code == 200
    view_id = view_response.json()["id"]

    response = client.post("/feature-views/materialize", json={
        "feature_view_id": view_id
    })
    assert response.status_code == 200
    assert response.json()["status"] == "materialization_started"

def test_get_feature_view_data():
    # Create a view first
    view_response = client.post("/feature-views", json={
        "features": ["age", "income"],
        "source_query": "SELECT * FROM users",
        "freshness_minutes": 60
    })
    view_id = view_response.json()["id"]

    response = client.get(f"/feature-views/{view_id}/data?entity_id=user123")
    assert response.status_code == 200
    data = response.json()
    assert "user123" in data
    # The service returns random values for the requested features
    assert "age" in data["user123"]
    assert "income" in data["user123"]
