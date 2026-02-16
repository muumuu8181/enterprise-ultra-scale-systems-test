from fastapi import FastAPI, HTTPException
from typing import List, Dict, Optional
import os
import json
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from shared.schemas.models import TrafficCameraData

app = FastAPI(title="Smart City Urban API", version="0.1.0")

DATA_LAKE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
DATA_FILE = os.path.join(DATA_LAKE_DIR, "traffic_data.jsonl")

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart City Urban OS API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

def _read_data() -> List[TrafficCameraData]:
    data = []
    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r") as f:
        for line in f:
            try:
                # Pydantic v2: validate_json
                item = TrafficCameraData.model_validate_json(line)
                data.append(item)
            except Exception:
                continue
    return data

@app.get("/sensors", response_model=List[str])
def list_sensors():
    """List all unique sensor IDs found in the data lake."""
    data = _read_data()
    sensors = set(d.sensor_id for d in data)
    return list(sensors)

@app.get("/sensors/{sensor_id}/latest", response_model=TrafficCameraData)
def get_latest_sensor_data(sensor_id: str):
    """Get the most recent data point for a specific sensor."""
    data = _read_data()
    sensor_data = [d for d in data if d.sensor_id == sensor_id]

    if not sensor_data:
        raise HTTPException(status_code=404, detail="Sensor not found or no data available")

    # Sort by timestamp descending
    sensor_data.sort(key=lambda x: x.timestamp, reverse=True)
    return sensor_data[0]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
