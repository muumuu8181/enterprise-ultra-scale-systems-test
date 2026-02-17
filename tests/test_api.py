from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to AI/ML Integration Platform"}

def test_create_training_job():
    response = client.post(
        "/training/jobs",
        json={
            "dataset_path": "s3://data/mnist",
            "model_type": "resnet",
            "hyperparams": {"lr": 0.01}
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"

def test_create_feature_set():
    response = client.post(
        "/features/sets",
        json={
            "name": "user_features",
            "entities": ["user_id"],
            "features": [{"name": "age", "type": "int"}]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "user_features"
    assert data["status"] == "created"
