import subprocess
import time
import requests
import os
import signal
import sys
import shutil

def main():
    if not shutil.which("mosquitto"):
        print("Error: 'mosquitto' binary not found. This test requires a local MQTT broker.")
        sys.exit(1)

    processes = []
    try:
        print("Starting Mosquitto...")
        # Start mosquitto in background
        mosquitto = subprocess.Popen(["mosquitto", "-c", "mosquitto/config/mosquitto.conf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processes.append(mosquitto)
        time.sleep(2) # Wait for broker to start

        print("Starting Data Ingestion Service...")
        ingestion = subprocess.Popen(["python", "services/data-ingestion/main.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(ingestion)
        time.sleep(2)

        print("Starting Traffic Collector (Simulator)...")
        collector = subprocess.Popen(["python", "services/traffic-collector/main.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(collector)

        print("Waiting 10 seconds for data collection...")
        time.sleep(10)

        print("Starting Urban API...")
        api = subprocess.Popen(["uvicorn", "services.urban-api.main:app", "--host", "0.0.0.0", "--port", "8000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(api)
        time.sleep(5) # Wait for API to start

        print("Verifying API endpoints...")

        # Test 1: List sensors
        try:
            resp = requests.get("http://localhost:8000/sensors")
            if resp.status_code == 200:
                sensors = resp.json()
                print(f"SUCCESS: /sensors returned {len(sensors)} sensors: {sensors}")
                if len(sensors) == 0:
                     print("WARNING: No sensors found. Data might not have flowed correctly.")
            else:
                print(f"FAILURE: /sensors returned {resp.status_code}")
                print(resp.text)
        except Exception as e:
            print(f"FAILURE: Could not connect to API: {e}")

        # Test 2: Get latest data for a sensor (if any exist)
        if sensors:
            sensor_id = sensors[0]
            try:
                resp = requests.get(f"http://localhost:8000/sensors/{sensor_id}/latest")
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"SUCCESS: /sensors/{sensor_id}/latest returned data.")
                    print(f"  Vehicle Count: {data.get('vehicle_count')}")
                    print(f"  Congestion: {data.get('congestion_level')}")
                else:
                    print(f"FAILURE: /sensors/{sensor_id}/latest returned {resp.status_code}")
            except Exception as e:
                print(f"FAILURE: Could not connect to API: {e}")

    finally:
        print("Stopping all services...")
        for p in processes:
            p.terminate()
            try:
                p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                p.kill()

        # Ensure mosquitto is really dead (sometimes Popen terminate isn't enough if it spawned children)
        subprocess.run(["pkill", "mosquitto"], stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    main()
