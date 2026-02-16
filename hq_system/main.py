import sys
import os

# Add the root directory to sys.path to allow importing 'shared'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from shared.models import Product, Transaction
from hq_system.forecasting import predict_order
from typing import List

app = FastAPI(title="HQ System")

# In-memory storage
products_db: List[Product] = []
sales_db: List[Transaction] = []

@app.post("/products", response_model=Product)
def add_product(product: Product):
    # Check for duplicate ID
    for p in products_db:
        if p.id == product.id:
            raise HTTPException(status_code=400, detail="Product ID already exists")
    products_db.append(product)
    return product

@app.get("/products", response_model=List[Product])
def list_products():
    return products_db

@app.post("/sales", status_code=201)
def receive_sales(transactions: List[Transaction]):
    """Receive synced sales from stores."""
    count = 0
    for txn in transactions:
        # Avoid duplicates (idempotency)
        if not any(t.id == txn.id for t in sales_db):
            sales_db.append(txn)
            count += 1
    return {"received": count, "total_stored": len(sales_db)}

@app.get("/report")
def get_report():
    total_revenue = sum(t.total for t in sales_db)
    return {
        "total_revenue": total_revenue,
        "transaction_count": len(sales_db)
    }

@app.get("/predict/{product_id}")
def get_prediction(product_id: str):
    qty = predict_order(product_id, sales_db)
    return {"product_id": product_id, "suggested_reorder": qty}
