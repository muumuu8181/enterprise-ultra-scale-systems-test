from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from shared.models import Base, Product, Transaction, TransactionItem, ProductCreate, ProductRead, TransactionCreate, TransactionRead
from .database import engine, init_db, get_db

app = FastAPI(title="Store System (POS)")

@app.on_event("startup")
def on_startup():
    init_db()

# For Initial Data Loading
@app.post("/products", response_model=ProductRead)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/pos/scan/{jan_code}", response_model=ProductRead)
def scan_product(jan_code: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.jan_code == jan_code).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/pos/checkout", response_model=TransactionRead)
def checkout(tx_data: TransactionCreate, db: Session = Depends(get_db)):
    total_amount = 0
    transaction_items = []

    # 1. Validate Items & Calculate Total
    for item_req in tx_data.items:
        product = db.query(Product).filter(Product.id == item_req.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product ID {item_req.product_id} not found")

        amount = product.price * item_req.quantity
        total_amount += amount

        transaction_items.append(TransactionItem(
            product_id=product.id,
            product_name=product.name,
            quantity=item_req.quantity,
            unit_price=product.price
        ))

    # 2. Create Transaction
    db_tx = Transaction(
        store_id=tx_data.store_id,
        timestamp=datetime.utcnow(),
        total_amount=total_amount,
        payment_method=tx_data.payment_method,
        synced=False
    )
    db.add(db_tx)
    db.flush() # get ID

    # 3. Save Items
    for item in transaction_items:
        item.transaction_id = db_tx.id
        db.add(item)

    db.commit()
    db.refresh(db_tx)
    return db_tx
