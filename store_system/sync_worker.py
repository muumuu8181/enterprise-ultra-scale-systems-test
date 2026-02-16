import requests
import time
import sys
import os

STORE_API = "http://localhost:8001"
HQ_API = "http://localhost:8000"

def run_sync():
    """
    Syncs transactions from Store to HQ.
    """
    print("Starting sync...")

    # 1. Get unsynced transactions from Store
    try:
        response = requests.get(f"{STORE_API}/transactions", params={"synced": False})
        response.raise_for_status()
        unsynced_txns = response.json()
    except Exception as e:
        print(f"Error fetching from Store: {e}")
        return

    if not unsynced_txns:
        print("No unsynced transactions found.")
        return

    print(f"Found {len(unsynced_txns)} unsynced transactions.")

    # 2. Push to HQ
    try:
        # Convert datetime strings back if needed, but requests.json() handles basic JSON types.
        # HQ expects a list of transactions.
        response = requests.post(f"{HQ_API}/sales", json=unsynced_txns)
        response.raise_for_status()
        print("Successfully pushed to HQ.")
    except Exception as e:
        print(f"Error pushing to HQ: {e}")
        return

    # 3. Mark as synced in Store
    for txn in unsynced_txns:
        try:
            requests.put(f"{STORE_API}/transactions/{txn['id']}/synced")
            print(f"Marked txn {txn['id']} as synced.")
        except Exception as e:
            print(f"Error marking txn {txn['id']} as synced: {e}")

if __name__ == "__main__":
    # In a real system, this would loop. For the demo, run once.
    run_sync()
