import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Set env var (though we will override engine anyway)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Create test engine with StaticPool to share connection across threads/requests
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Monkey patch src.database BEFORE importing src.main
import src.database
src.database.engine = test_engine
src.database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

from src.database import Base, get_db
from src.main import app
from src.models.gallery_models import Artwork, Exhibition, Sale, ArtworkLocation, ExhibitionStatus, SaleType, PaymentStatus

# Create tables
Base.metadata.create_all(bind=test_engine)

# Dependency override
def override_get_db():
    db = src.database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def db():
    db = src.database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_create_exhibition():
    response = client.post(
        "/api/v1/exhibitions/create",
        json={
            "gallery_id": 1,
            "title": "Modern Art",
            "status": "planning"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Modern Art"
    assert data["status"] == "planning"

def test_get_artworks(db):
    # Seed data
    artwork = Artwork(
        title="Starry Night",
        artist_id=1,
        medium="Oil",
        price=1000000.0,
        location=ArtworkLocation.GALLERY
    )
    db.add(artwork)
    db.commit()

    response = client.get("/api/v1/artworks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Starry Night"

def test_record_sale(db):
    # Seed artwork
    artwork = Artwork(
        title="Mona Lisa Copy",
        artist_id=2,
        price=500.0,
        location=ArtworkLocation.GALLERY
    )
    db.add(artwork)
    db.commit()
    db.refresh(artwork)

    response = client.post(
        "/api/v1/sales/record",
        json={
            "artwork_id": artwork.id,
            "buyer_id": 101,
            "sale_type": "private",
            "hammer_price": 500.0,
            "commission_pct": 10.0
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total_amount"] == 550.0

    # Verify artwork status updated
    db.refresh(artwork)
    assert artwork.location == ArtworkLocation.SOLD

def test_appraise_artwork(db):
    artwork = Artwork(
        title="Unknown",
        artist_id=3,
        price=100.0
    )
    db.add(artwork)
    db.commit()
    db.refresh(artwork)

    response = client.post(f"/api/v1/artworks/{artwork.id}/appraise")
    assert response.status_code == 200
    data = response.json()
    assert data["estimated_value"] > 100.0
