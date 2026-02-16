import time
import os
import requests
from sqlalchemy.orm import Session
from .database import SessionLocal
from shared.models import Transaction, TransactionSync, TransactionItemRead

HQ_URL = os.getenv("HQ_URL", "http://localhost:8000")

def sync_transactions():
    db = SessionLocal()
    try:
        # 1. Get unsynced transactions
        unsynced_txs = db.query(Transaction).filter(Transaction.synced == False).limit(50).all()

        if not unsynced_txs:
            # print("No unsynced transactions found.")
            return

        sync_payload = []
        for tx in unsynced_txs:
            # Convert to Sync Model
            items = []
            for item in tx.items:
                items.append(TransactionItemRead(
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price
                ))

            sync_payload.append(TransactionSync(
                store_id=tx.store_id,
                timestamp=tx.timestamp,
                total_amount=tx.total_amount,
                payment_method=tx.payment_method,
                items=items
            ))

        # 2. Send to HQ
        # Use model_dump for each item in list? No, requests takes json=dict
        payload_data = [t.model_dump(mode='json') for t in sync_payload]

        try:
            response = requests.post(f"{HQ_URL}/sync/sales", json=payload_data)
            response.raise_for_status()

            # 3. Mark as synced
            print(f"Successfully synced {len(unsynced_txs)} transactions.")
            for tx in unsynced_txs:
                tx.synced = True
            db.commit()

        except Exception as e:
            print(f"Failed to sync: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    print("Starting Sync Worker...")
    while True:
        sync_transactions()
        time.sleep(5)
