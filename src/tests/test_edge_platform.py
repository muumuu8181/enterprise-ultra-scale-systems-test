from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.v1.data import router
from src.models.edge_data import EdgeDataStream, LocalInference, DataPolicy
import sys
import os

# Add src to python path if not already there, for correct imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_models_exist():
    assert EdgeDataStream.__tablename__ == "edge_data_streams"
    assert LocalInference.__tablename__ == "local_inferences"
    assert DataPolicy.__tablename__ == "data_policies"

def test_stream_configure():
    response = client.post("/streams/configure", json={
        "device_id": "dev1",
        "stream_type": "video",
        "ingestion_rate": 10.5,
        "processing_mode": "local"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_inference_push():
    response = client.post("/inference/models/push", json={
        "model_id": "mod1",
        "device_ids": ["dev1", "dev2"]
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["success"] == True

def test_get_stream_stats():
    response = client.get("/streams/1/stats")
    assert response.status_code == 200
    assert response.json()["stream_id"] == 1

def test_get_storage_usage():
    response = client.get("/devices/dev1/local-storage-usage")
    assert response.status_code == 200
    assert response.json()["device_id"] == "dev1"
