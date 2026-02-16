import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared.models import Base, Product, Transaction, TransactionSync, TransactionItemRead
from hq_system.main import app as hq_app
from hq_system.database import get_db as hq_get_db
from store_system.main import app as store_app
from store_system.database import get_db as store_get_db

# Use separate DBs for test
HQ_DB_URL = "sqlite:///:memory:"
STORE_DB_URL = "sqlite:///:memory:"

hq_engine = create_engine(
    HQ_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
store_engine = create_engine(
    STORE_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

HQ_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=hq_engine)
Store_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=store_engine)

# Overrides
def override_hq_get_db():
    db = HQ_TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_store_get_db():
    db = Store_TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

hq_app.dependency_overrides[hq_get_db] = override_hq_get_db
store_app.dependency_overrides[store_get_db] = override_store_get_db

@pytest.fixture(scope="module")
def setup_databases():
    Base.metadata.create_all(bind=hq_engine)
    Base.metadata.create_all(bind=store_engine)
    yield
    Base.metadata.drop_all(bind=hq_engine)
    Base.metadata.drop_all(bind=store_engine)

def test_full_flow(setup_databases):
    hq_client = TestClient(hq_app)
    store_client = TestClient(store_app)

    # 1. Create Product in HQ
    product_data = {"jan_code": "4901234567890", "name": "Green Tea", "price": 150}
    resp = hq_client.post("/products", json=product_data)
    assert resp.status_code == 200
    hq_product = resp.json()
    assert hq_product["name"] == "Green Tea"

    # 2. Simulate Sync Down (Create same product in Store)
    resp = store_client.post("/products", json=product_data)
    assert resp.status_code == 200
    store_product = resp.json()

    # 3. Scan at Store
    resp = store_client.get(f"/pos/scan/{product_data['jan_code']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Green Tea"
    scanned_product_id = resp.json()["id"]

    # 4. Checkout at Store
    checkout_data = {
        "store_id": "store_001",
        "payment_method": "cash",
        "items": [
            {"product_id": scanned_product_id, "quantity": 2}
        ]
    }
    resp = store_client.post("/pos/checkout", json=checkout_data)
    assert resp.status_code == 200
    tx_data = resp.json()
    assert tx_data["total_amount"] == 300
    assert tx_data["synced"] == False

    # 5. Sync Up (Edge -> HQ)
    # Fetch unsynced from Store DB directly
    db = Store_TestingSessionLocal()
    unsynced = db.query(Transaction).filter(Transaction.synced == False).all()
    assert len(unsynced) == 1

    tx = unsynced[0]
    items = [TransactionItemRead(product_name=i.product_name, quantity=i.quantity, unit_price=i.unit_price) for i in tx.items]
    sync_obj = TransactionSync(
        store_id=tx.store_id,
        timestamp=tx.timestamp,
        total_amount=tx.total_amount,
        payment_method=tx.payment_method,
        items=items
    )

    # Send to HQ via TestClient
    payload = [sync_obj.model_dump(mode='json')]
    resp = hq_client.post("/sync/sales", json=payload)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Synced 1 transactions"

    # Mark as synced in Store (Manual step in test)
    tx.synced = True
    db.commit()
    db.close()

    # 6. Verify in HQ (Forecast)
    resp = hq_client.get("/forecast/Green Tea")
    assert resp.status_code == 200
    data = resp.json()
    assert data["product"] == "Green Tea"
    assert data["history_count"] == 1
    assert data["forecast"] == 2 # 2 units sold / 1 transaction = 2
