import time
import random
import urllib.request
import json
import sys

# Configuration
EQUIPMENT_ID = "EQP01"
BASE_URL = "http://localhost:8000/api/v1/equipment"

def set_status(eqp_id, status):
    # FastAPI expects 'status' as a query parameter by default for Enum/simple types
    url = f"{BASE_URL}/{eqp_id}/status?status={status}"
    req = urllib.request.Request(url, method='PUT')
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print(f"Successfully set {eqp_id} to {status}")
            else:
                print(f"Failed to set {eqp_id} to {status}: {response.status}")
    except Exception as e:
        print(f"Error communicating with server: {e}")

def simulate():
    print(f"Starting SECS/GEM Simulation for {EQUIPMENT_ID}...")
    print("Press Ctrl+C to stop.")

    try:
        # Loop for a bit to demonstrate
        for i in range(5):
            temp = random.normalvariate(100, 5)
            print(f"[{i+1}] Measured Temperature: {temp:.2f} C")

            if temp > 108:
                print(f"!!! ALARM: Temperature Exceeded Threshold (108). Triggering FDC...")
                set_status(EQUIPMENT_ID, "DOWN")

            # Simulate a "Repair" if it drops low enough just for demo?
            # No, let's just keep it simple.

            time.sleep(1)

    except KeyboardInterrupt:
        print("Simulation stopped.")

if __name__ == "__main__":
    # Ensure we wait for server to start if run immediately
    time.sleep(2)
    simulate()
