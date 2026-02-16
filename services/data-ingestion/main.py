import json
import os
import sys
from datetime import datetime
import paho.mqtt.client as mqtt
from pydantic import ValidationError

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from shared.schemas.models import TrafficCameraData

# Configuration
BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
TOPIC_SUBSCRIPTION = "sensors/traffic/#"
DATA_LAKE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
DATA_FILE = os.path.join(DATA_LAKE_DIR, "traffic_data.jsonl")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(TOPIC_SUBSCRIPTION)
        print(f"Subscribed to {TOPIC_SUBSCRIPTION}")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        print(f"Received message on {msg.topic}: {payload}")

        # Validate data
        try:
            traffic_data = TrafficCameraData.model_validate_json(payload)
        except ValidationError as e:
            print(f"Validation Error: {e}")
            return

        # "Data Lake" Storage (Append to JSONL)
        # In a real system, this would write to S3/HDFS/Parquet
        with open(DATA_FILE, "a") as f:
            f.write(traffic_data.model_dump_json() + "\n")

        print(f"Stored data for sensor {traffic_data.sensor_id}")

    except Exception as e:
        print(f"Error processing message: {e}")

def main():
    # Ensure data directory exists
    os.makedirs(DATA_LAKE_DIR, exist_ok=True)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connecting to MQTT Broker at {BROKER_HOST}:{BROKER_PORT}...")
    try:
        client.connect(BROKER_HOST, BROKER_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Could not connect to MQTT Broker: {e}")

if __name__ == "__main__":
    main()
