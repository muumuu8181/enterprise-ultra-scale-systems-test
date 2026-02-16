from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from shared.models import Base, Product, Transaction, TransactionItem, ProductCreate, ProductRead, TransactionSync
from .database import engine, init_db, get_db
from .ai import predict_demand

app = FastAPI(title="HQ System")

# Initialize DB on startup
@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/products", response_model=ProductRead)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products", response_model=List[ProductRead])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@app.post("/sync/sales")
def sync_sales(transactions: List[TransactionSync], db: Session = Depends(get_db)):
    count = 0
    for tx_data in transactions:
        # Create Transaction record in HQ DB
        db_tx = Transaction(
            store_id=tx_data.store_id,
            timestamp=tx_data.timestamp,
            total_amount=tx_data.total_amount,
            payment_method=tx_data.payment_method,
            synced=True # Marked as synced (it is the master record now)
        )
        db.add(db_tx)
        db.flush() # get ID

        # Create Items
        for item_data in tx_data.items:
            db_item = TransactionItem(
                transaction_id=db_tx.id,
                product_id=0, # Placeholder as ID might differ across stores/HQ if not careful. Using name for simple receipt matching.
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price
            )
            db.add(db_item)

        count += 1

    db.commit()
    return {"message": f"Synced {count} transactions"}

@app.get("/forecast/{product_name}")
def get_forecast(product_name: str, db: Session = Depends(get_db)):
    # Get Sales History
    items = db.query(TransactionItem).filter(TransactionItem.product_name == product_name).all()
    if not items:
        return {"product": product_name, "forecast": 0, "history_count": 0}

    # Simplified: history is just list of quantities sold per transaction
    history = [item.quantity for item in items]

    forecast = predict_demand(history)

    return {
        "product": product_name,
        "forecast": forecast,
        "history_count": len(history)
    }
