import time
import random
import json
import os
import sys
from datetime import datetime
import paho.mqtt.client as mqtt

# Add the project root to sys.path to allow importing from shared
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from shared.schemas.models import TrafficCameraData, SensorType

# Configuration
BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
TOPIC_BASE = "sensors/traffic"

# Simulated Sensors
SENSORS = [
    {"id": "cam_001", "lat": 35.6895, "lon": 139.6917},  # Tokyo
    {"id": "cam_002", "lat": 35.6890, "lon": 139.6920},
    {"id": "cam_003", "lat": 35.6900, "lon": 139.6910},
    {"id": "cam_004", "lat": 34.6937, "lon": 135.5023},  # Osaka
    {"id": "cam_005", "lat": 34.6940, "lon": 135.5030},
]

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}")

def generate_traffic_data(sensor_config):
    vehicle_count = random.randint(0, 50)
    avg_speed = random.uniform(10.0, 80.0)

    if vehicle_count < 10:
        congestion = "low"
    elif vehicle_count < 30:
        congestion = "medium"
    else:
        congestion = "high"
        avg_speed = random.uniform(5.0, 20.0) # Slower when congested

    data = TrafficCameraData(
        sensor_id=sensor_config["id"],
        sensor_type=SensorType.TRAFFIC_CAMERA,
        timestamp=datetime.utcnow(),
        location={"lat": sensor_config["lat"], "lon": sensor_config["lon"]},
        vehicle_count=vehicle_count,
        avg_speed_kmh=round(avg_speed, 2),
        congestion_level=congestion
    )
    return data

def main():
    # Use CallbackAPIVersion.VERSION2 for paho-mqtt 2.x
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect

    print(f"Connecting to MQTT Broker at {BROKER_HOST}:{BROKER_PORT}...")
    try:
        client.connect(BROKER_HOST, BROKER_PORT, 60)
        client.loop_start()
    except Exception as e:
        print(f"Could not connect to MQTT Broker: {e}")
        # For verification purposes, we might run this without a broker and just print
        # But let's assume we want to fail if no broker for now.
        return

    try:
        while True:
            for sensor in SENSORS:
                data = generate_traffic_data(sensor)
                topic = f"{TOPIC_BASE}/{sensor['id']}"
                # Pydantic v2 uses model_dump_json()
                payload = data.model_dump_json()

                client.publish(topic, payload)
                print(f"Published to {topic}: {payload}")

            time.sleep(5)
    except KeyboardInterrupt:
        print("Stopping simulation...")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
