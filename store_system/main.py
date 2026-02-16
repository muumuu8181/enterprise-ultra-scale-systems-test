import sys
import os
from datetime import datetime

# Add the root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from shared.models import Product, Transaction, SaleItem
from typing import List

app = FastAPI(title="Store System (Edge)")

# Local Storage
local_products: List[Product] = []
local_transactions: List[Transaction] = []

@app.post("/sync/products")
def sync_products(products: List[Product]):
    """Receive product updates from HQ."""
    global local_products
    # In a real system, this would merge/update SQLite
    local_products = products
    return {"status": "synced", "count": len(local_products)}

@app.get("/scan/{barcode}")
def scan_product(barcode: str):
    """Simulate barcode scanning."""
    product = next((p for p in local_products if p.id == barcode), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/checkout")
def checkout(items: List[SaleItem]):
    """Process a sale locally."""
    total = sum(item.price * item.quantity for item in items)

    # Generate Transaction
    txn = Transaction(
        id=f"txn_{len(local_transactions) + 1}_{int(datetime.now().timestamp())}",
        store_id="store_001",
        items=items,
        total=total,
        timestamp=datetime.now(),
        synced=False
    )

    local_transactions.append(txn)
    return txn

@app.get("/transactions")
def list_transactions(synced: bool = None):
    """List transactions, optionally filter by sync status."""
    if synced is None:
        return local_transactions
    return [t for t in local_transactions if t.synced == synced]

@app.put("/transactions/{txn_id}/synced")
def mark_synced(txn_id: str):
    """Mark a transaction as synced."""
    txn = next((t for t in local_transactions if t.id == txn_id), None)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    txn.synced = True
    return {"status": "updated"}
