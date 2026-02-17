import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.v1.keys import router
from src.services.crypto_service import CryptoService
from src.models.crypto_models import CryptoAlgorithm

app = FastAPI()
app.include_router(router)

client = TestClient(app)

@pytest.mark.asyncio
async def test_generate_keypair():
    service = CryptoService()
    keypair = await service.generate_keypair(CryptoAlgorithm.KYBER.value, 123)
    assert keypair.algorithm == CryptoAlgorithm.KYBER.value
    assert keypair.owner_id == 123
    assert keypair.public_key is not None

@pytest.mark.asyncio
async def test_hybrid_encrypt():
    service = CryptoService()
    plaintext = b"secret message"
    encrypted = await service.hybrid_encrypt(plaintext, "mock_pub_key")
    assert encrypted.ciphertext_uri.startswith("s3://")
    assert encrypted.algorithm == "hybrid-kyber-aes"

def test_api_generate_key():
    response = client.post("/keys/generate", json={"algorithm": "kyber", "owner_id": 99})
    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"] == "kyber"
    assert data["owner_id"] == 99
    assert "id" in data

def test_api_encrypt():
    response = client.post("/encrypt", json={"plaintext": "hello", "public_key": "abc"})
    assert response.status_code == 200
    data = response.json()
    assert "ciphertext_uri" in data
    assert "nonce" in data

def test_api_verify():
    response = client.post("/verify", json={"data": "test", "signature": "sig", "public_key": "pk"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
