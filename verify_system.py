import subprocess
import time
import requests
import sys

HQ_PORT = 8000
STORE_PORT = 8001
HQ_URL = f"http://localhost:{HQ_PORT}"
STORE_URL = f"http://localhost:{STORE_PORT}"

def start_server(app_path, port, name):
    print(f"Starting {name} on port {port}...")
    # Use sys.executable to ensure we use the same python environment
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", app_path, "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2) # Give it time to start
    if proc.poll() is not None:
        out, err = proc.communicate()
        print(f"Failed to start {name}: {err.decode()}")
        sys.exit(1)
    return proc

def main():
    hq_proc = start_server("hq_system.main:app", HQ_PORT, "HQ")
    store_proc = start_server("store_system.main:app", STORE_PORT, "Store")

    try:
        # 1. Add Product to HQ
        print("\n1. Adding Product to HQ...")
        prod = {"id": "123456", "name": "Onigiri", "price": 150.0, "category": "Food"}
        res = requests.post(f"{HQ_URL}/products", json=prod)
        if res.status_code != 200:
            print(f"Failed to add product: {res.text}")
            return
        print("Product added.")

        # 2. Sync Product to Store
        # (In reality, Store pulls or HQ pushes. Let's simulate HQ pushing to Store)
        print("\n2. Syncing Product to Store...")
        res = requests.post(f"{STORE_URL}/sync/products", json=[prod])
        if res.status_code != 200:
             print(f"Failed to sync product: {res.text}")
             return
        print("Product synced.")

        # 3. Perform Sale at Store
        print("\n3. Performing Sale at Store...")
        # First scan
        res = requests.get(f"{STORE_URL}/scan/123456")
        if res.status_code != 200:
             print(f"Failed to scan: {res.text}")
             return
        item = res.json()
        print(f"Scanned: {item['name']}")

        # Checkout
        sale_items = [{"product_id": item["id"], "quantity": 2, "price": item["price"]}]
        res = requests.post(f"{STORE_URL}/checkout", json=sale_items)
        if res.status_code != 200:
             print(f"Failed to checkout: {res.text}")
             return
        txn = res.json()
        print(f"Transaction Created: {txn['id']}")

        # 4. Trigger Sync Worker
        print("\n4. Triggering Sync Worker...")
        # We run the script directly
        subprocess.run([sys.executable, "store_system/sync_worker.py"], check=True)

        # 5. Verify Sale in HQ
        print("\n5. Verifying Sale in HQ...")
        res = requests.get(f"{HQ_URL}/report")
        report = res.json()
        print(f"HQ Report: {report}")
        if report["transaction_count"] != 1:
            print("FAILURE: Transaction count mismatch in HQ")
            sys.exit(1)

        # 6. Verify Forecasting
        print("\n6. Verifying Forecasting...")
        res = requests.get(f"{HQ_URL}/predict/123456")
        pred = res.json()
        print(f"Prediction: {pred}")
        if pred["suggested_reorder"] <= 0:
             print("FAILURE: Prediction logic seems off")
             sys.exit(1)

        print("\nSUCCESS: All steps passed.")

    except Exception as e:
        print(f"\nEXCEPTION: {e}")
    finally:
        print("\nShutting down servers...")
        hq_proc.terminate()
        store_proc.terminate()
        hq_proc.wait()
        store_proc.wait()

if __name__ == "__main__":
    main()
