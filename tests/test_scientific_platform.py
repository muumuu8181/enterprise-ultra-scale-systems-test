from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Scientific Computing Platform"}

def test_submit_job():
    response = client.post("/api/v1/jobs/submit", json={
        "user_id": "user123",
        "job_type": "simulation",
        "priority": 1,
        "nodes_requested": 2,
        "gpus_requested": 0,
        "walltime_sec": 3600
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user123"
    assert data["job_type"] == "simulation"
    assert "id" in data
    return data["id"]

def test_get_job_status():
    # Submit a job first
    job_id = test_submit_job()

    response = client.get(f"/api/v1/jobs/{job_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert "status" in data

def test_get_job_stdout():
    job_id = test_submit_job()
    response = client.get(f"/api/v1/jobs/{job_id}/stdout")
    assert response.status_code == 200
    assert "stdout" in response.json()

def test_get_job_output_files():
    job_id = test_submit_job()
    response = client.get(f"/api/v1/jobs/{job_id}/output-files")
    assert response.status_code == 200
    assert "files" in response.json()

def test_cancel_job():
    job_id = test_submit_job()
    response = client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

def test_queue_position():
    response = client.get("/api/v1/jobs/queue/position")
    assert response.status_code == 200
    assert "queue_depth" in response.json()

def test_get_clusters_utilization():
    response = client.get("/api/v1/clusters/clusterA/utilization")
    assert response.status_code == 200
    data = response.json()
    assert data["cluster_id"] == "clusterA"
    assert "cpu_usage_percent" in data

def test_get_clusters_queue():
    response = client.get("/api/v1/clusters/clusterA/queue")
    assert response.status_code == 200
    assert "pending_jobs" in response.json()

def test_resource_request():
    response = client.post("/api/v1/clusters/resource-request", json={
        "cluster_id": "clusterA",
        "nodes": 5,
        "duration_sec": 3600,
        "project_id": "proj1"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

def test_get_reservations():
    response = client.get("/api/v1/clusters/reservations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
